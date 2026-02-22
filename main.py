#!/usr/bin/env python3
from __future__ import annotations

import argparse
import calendar
import json
import logging
import os
import re
import smtplib
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from html import escape, unescape
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests
import yaml
from dotenv import load_dotenv
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

STATE_FILE = Path("state.json")
OUTBOX_DIR = Path("outbox")
LOGS_DIR = Path("logs")
LOG_FILE = LOGS_DIR / "veille.log"

DEFAULT_MAX_ITEMS = 10
REQUEST_TIMEOUT = (5, 20)
ARTICLE_TIMEOUT = (5, 15)
FEED_RETRIES = 2
USER_AGENT = "VeilleAgent/1.0"

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
}

DAY_CODES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_ALIASES = {
    "MON": "Mon",
    "MONDAY": "Mon",
    "LUN": "Mon",
    "LUNDI": "Mon",
    "TUE": "Tue",
    "TUESDAY": "Tue",
    "MARDI": "Tue",
    "WED": "Wed",
    "WEDNESDAY": "Wed",
    "MER": "Wed",
    "MERCREDI": "Wed",
    "THU": "Thu",
    "THURSDAY": "Thu",
    "JEU": "Thu",
    "JEUDI": "Thu",
    "FRI": "Fri",
    "FRIDAY": "Fri",
    "VEN": "Fri",
    "VENDREDI": "Fri",
    "SAT": "Sat",
    "SATURDAY": "Sat",
    "SAM": "Sat",
    "SAMEDI": "Sat",
    "SUN": "Sun",
    "SUNDAY": "Sun",
    "DIM": "Sun",
    "DIMANCHE": "Sun",
}


@dataclass(frozen=True)
class TopicConfig:
    key: str
    title: str
    days: set[str]
    sources: list[str]
    max_items: int | None


@dataclass(frozen=True)
class AppConfig:
    timezone: str
    max_items: int
    topics: dict[str, TopicConfig]


@dataclass
class FeedItem:
    title: str
    link: str
    source: str
    published: datetime
    raw_text: str
    summary: str = ""


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str
    timeout_seconds: int


class JsonFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()
        self._standard = set(vars(logging.makeLogRecord({})).keys())

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }
        for key, value in record.__dict__.items():
            if key in self._standard or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agent de veille RSS -> email quotidien")
    parser.add_argument("--dry-run", action="store_true", help="Écrit l'email dans outbox/ sans envoi SMTP")
    parser.add_argument("--date", dest="date_str", help="Date d'exécution YYYY-MM-DD (sinon aujourd'hui)")
    parser.add_argument("--topic", help="Clé du topic à forcer (ou titre exact)")
    parser.add_argument("--config", default="config.yaml", help="Chemin du fichier config YAML")
    return parser.parse_args(argv)


def ensure_directories() -> None:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("veille")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = JsonFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ValueError(f"Fichier de config introuvable: {path}")

    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("config.yaml invalide: structure racine attendue de type mapping")

    settings = content.get("settings", {})
    if settings is None:
        settings = {}
    if not isinstance(settings, dict):
        raise ValueError("config.yaml invalide: settings doit être un mapping")

    tz_name = str(settings.get("timezone", "Europe/Paris"))
    max_items = parse_int(settings.get("max_items", DEFAULT_MAX_ITEMS), "settings.max_items")
    max_items = max(5, min(15, max_items))

    topics_raw = content.get("topics")
    if not isinstance(topics_raw, dict) or not topics_raw:
        raise ValueError("config.yaml invalide: topics doit contenir au moins un topic")

    topics: dict[str, TopicConfig] = {}
    for key, value in topics_raw.items():
        topics[str(key)] = parse_topic_config(str(key), value)

    return AppConfig(timezone=tz_name, max_items=max_items, topics=topics)


def parse_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} doit être un entier") from exc


def parse_topic_config(key: str, raw: Any) -> TopicConfig:
    if not isinstance(raw, dict):
        raise ValueError(f"topic '{key}' invalide: mapping attendu")

    title = str(raw.get("title", key)).strip()
    days_raw = raw.get("days", [])
    sources_raw = raw.get("sources", [])

    if not isinstance(days_raw, list) or not days_raw:
        raise ValueError(f"topic '{key}' invalide: days doit être une liste non vide")
    if not isinstance(sources_raw, list) or not sources_raw:
        raise ValueError(f"topic '{key}' invalide: sources doit être une liste non vide")

    days = {normalize_day(str(day)) for day in days_raw}
    sources = [str(src).strip() for src in sources_raw if str(src).strip()]
    if not sources:
        raise ValueError(f"topic '{key}' invalide: aucune source RSS valide")

    max_items: int | None = None
    if "max_items" in raw and raw["max_items"] is not None:
        max_items = max(5, min(15, parse_int(raw["max_items"], f"topics.{key}.max_items")))

    return TopicConfig(key=key, title=title, days=days, sources=sources, max_items=max_items)


def normalize_day(day: str) -> str:
    token = re.sub(r"[^A-Za-zÀ-ÿ]", "", day).upper()
    if token in DAY_ALIASES:
        return DAY_ALIASES[token]
    if len(token) >= 3 and token[:3] in DAY_ALIASES:
        return DAY_ALIASES[token[:3]]
    raise ValueError(f"Jour invalide dans config: '{day}'")


def parse_run_date(date_str: str | None, timezone_name: str) -> date:
    if date_str:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("Format de --date invalide (attendu: YYYY-MM-DD)") from exc

    tz = safe_timezone(timezone_name)
    return datetime.now(tz).date()


def safe_timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def select_topics(config: AppConfig, topic_arg: str | None, run_date: date) -> list[TopicConfig]:
    if topic_arg:
        key_match = config.topics.get(topic_arg)
        if key_match:
            return [key_match]
        for topic in config.topics.values():
            if topic.title.lower() == topic_arg.lower():
                return [topic]
        raise ValueError(f"Topic inconnu: '{topic_arg}'")

    day_code = DAY_CODES[run_date.weekday()]
    selected = [topic for topic in config.topics.values() if day_code in topic.days]
    return selected


def load_state(path: Path, logger: logging.Logger) -> set[str]:
    if not path.exists():
        logger.info("state_created", extra={"path": str(path)})
        return set()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("state_corrupted_reset", extra={"path": str(path)})
        return set()

    links = data.get("sent_links", [])
    if not isinstance(links, list):
        logger.warning("state_invalid_reset", extra={"path": str(path)})
        return set()
    return {str(link) for link in links if isinstance(link, str)}


def save_state(path: Path, sent_links: set[str]) -> None:
    payload = {
        "sent_links": sorted(sent_links),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    if not parts.scheme or not parts.netloc:
        return url.strip()

    filtered_query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        low_key = key.lower()
        if low_key.startswith("utm_") or low_key in TRACKING_QUERY_KEYS:
            continue
        filtered_query.append((key, value))
    query = urlencode(filtered_query, doseq=True)

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def fetch_feed(url: str, logger: logging.Logger) -> feedparser.FeedParserDict | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"}
    for attempt in range(1, FEED_RETRIES + 2):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if getattr(parsed, "bozo", False):
                logger.warning(
                    "feed_bozo",
                    extra={"source_url": url, "detail": str(getattr(parsed, "bozo_exception", "unknown"))},
                )
            return parsed
        except requests.RequestException as exc:
            logger.warning(
                "feed_retry",
                extra={"source_url": url, "attempt": attempt, "error": str(exc)},
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "feed_parse_retry",
                extra={"source_url": url, "attempt": attempt, "error": str(exc)},
            )

        if attempt <= FEED_RETRIES:
            time.sleep(attempt)

    logger.error("feed_failed", extra={"source_url": url})
    return None


def collect_topic_items(topic: TopicConfig, sent_links: set[str], default_max: int, logger: logging.Logger) -> list[FeedItem]:
    collected: list[FeedItem] = []
    local_seen: set[str] = set()

    for source_url in topic.sources:
        parsed = fetch_feed(source_url, logger)
        if parsed is None:
            continue

        feed_title = str(parsed.feed.get("title") or urlsplit(source_url).netloc)
        entries: Iterable[Any] = parsed.entries if parsed.entries else []

        for entry in entries:
            item = entry_to_item(entry, feed_title)
            if item is None:
                continue
            normalized = canonicalize_url(item.link)
            if not normalized:
                continue
            if normalized in sent_links or normalized in local_seen:
                continue
            item.link = normalized
            local_seen.add(normalized)
            collected.append(item)

    collected.sort(key=lambda item: item.published, reverse=True)
    limit = topic.max_items if topic.max_items is not None else default_max
    limit = max(5, min(15, limit))
    return collected[:limit]


def entry_to_item(entry: Any, feed_title: str) -> FeedItem | None:
    link = str(entry.get("link", "")).strip()
    title = str(entry.get("title", "")).strip()
    if not link or not title:
        return None

    source = feed_title
    source_data = entry.get("source")
    if isinstance(source_data, dict):
        source_title = str(source_data.get("title", "")).strip()
        if source_title:
            source = source_title

    raw_text = extract_entry_text(entry)
    published = parse_entry_datetime(entry)

    return FeedItem(
        title=title,
        link=link,
        source=source,
        published=published,
        raw_text=raw_text,
    )


def parse_entry_datetime(entry: Any) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)

    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if raw:
            try:
                dt = parsedate_to_datetime(str(raw))
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except (TypeError, ValueError):
                continue

    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def extract_entry_text(entry: Any) -> str:
    for key in ("summary", "description"):
        value = entry.get(key)
        if value:
            return html_to_text(str(value))

    content = entry.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and first.get("value"):
            return html_to_text(str(first["value"]))
    return ""


def html_to_text(value: str) -> str:
    without_tags = TAG_RE.sub(" ", value)
    plain = unescape(without_tags)
    return SPACE_RE.sub(" ", plain).strip()


def summarize_local(text: str, title: str) -> str:
    source = text.strip()
    if not source:
        base = f"Le flux ne fournit pas de description détaillée pour « {title} »."
        return enforce_summary_shape(base, title)

    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(source) if s.strip()]
    if not sentences:
        return enforce_summary_shape(source[:280].strip(), title)

    target = sentences[:3]
    if len(target) == 1 and len(source) > 220:
        target = [source[:220].strip()]
    summary = " ".join(target).strip()
    if len(summary) > 520:
        summary = summary[:517].rstrip() + "..."
    return enforce_summary_shape(summary, title)


def enforce_summary_shape(summary: str, title: str) -> str:
    cleaned = summary.strip()
    if not cleaned:
        cleaned = f"Résumé indisponible pour « {title} »."
    sentences = [s.strip() for s in SENTENCE_SPLIT_RE.split(cleaned) if s.strip()]
    if len(sentences) >= 3:
        return " ".join(sentences[:3])
    if len(sentences) == 2:
        return " ".join(sentences)
    if len(sentences) == 1:
        return (
            f"{sentences[0]} "
            "Les détails opérationnels restent à valider dans le contenu complet."
        )
    return (
        f"Résumé indisponible pour « {title} ». "
        "Les détails opérationnels restent à valider dans le contenu complet."
    )


def fetch_article_excerpt(url: str, logger: logging.Logger) -> str:
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=ARTICLE_TIMEOUT)
        response.raise_for_status()
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", response.text, flags=re.IGNORECASE | re.DOTALL)
        excerpt = " ".join(html_to_text(chunk) for chunk in paragraphs[:4])
        return excerpt.strip()
    except requests.RequestException as exc:
        logger.info("article_fallback_unavailable", extra={"url": url, "error": str(exc)})
        return ""


def load_openai_config() -> OpenAIConfig | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    timeout = os.getenv("OPENAI_TIMEOUT", "20").strip()
    timeout_seconds = 20
    if timeout.isdigit():
        timeout_seconds = int(timeout)
    return OpenAIConfig(api_key=api_key, model=model, timeout_seconds=timeout_seconds)


def maybe_enhance_summary(item: FeedItem, local_summary: str, openai_cfg: OpenAIConfig | None, logger: logging.Logger) -> str:
    if openai_cfg is None:
        return local_summary

    prompt = (
        "Tu es un analyste veille. Résume le contenu suivant en 2 ou 3 phrases max, ton factuel, en français. "
        "Ne rajoute aucune information absente du texte.\n\n"
        f"Titre: {item.title}\n"
        f"Contenu: {item.raw_text[:3500] or local_summary}"
    )
    payload = {
        "model": openai_cfg.model,
        "messages": [
            {"role": "system", "content": "Tu rédiges des résumés de veille concis et fiables."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 170,
    }
    headers = {
        "Authorization": f"Bearer {openai_cfg.api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=openai_cfg.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        summary = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )
        if summary:
            return enforce_summary_shape(summary, item.title)
    except requests.RequestException as exc:
        logger.warning("openai_summary_failed", extra={"error": str(exc), "url": item.link})
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("openai_summary_invalid_response", extra={"error": str(exc), "url": item.link})

    return enforce_summary_shape(local_summary, item.title)


def build_signal_vs_noise(items: list[FeedItem]) -> tuple[str, str]:
    corpus = " ".join((f"{item.title} {item.summary}".lower() for item in items))
    important = "Les publications convergent vers des cas d'usage applicables (process, coûts, délais), avec des signaux exploitables rapidement."
    ignore = "Une partie du flux ressemble à des annonces marketing sans métriques (ROI, lead time, qualité) : faible priorité tant qu'aucune preuve terrain."

    if any(term in corpus for term in ("forecast", "prediction", "demand", "planification", "s&op")):
        important = "Le signal principal porte sur la prévision et la planification pilotées par données, avec impact direct attendu sur les stocks et le service."
    elif any(term in corpus for term in ("robot", "automation", "warehouse", "amr")):
        important = "Le signal principal concerne l'automatisation opérationnelle (entrepôt, production, robotique), avec gains potentiels en productivité et sécurité."
    elif any(term in corpus for term in ("last mile", "delivery", "route", "transport")):
        important = "Le signal principal se situe sur l'optimisation transport/dernier kilomètre, levier direct sur coût de livraison et ponctualité."

    if any(term in corpus for term in ("sponsor", "launches", "announces", "partnership")):
        ignore = "À ignorer en priorité: annonces de partenariat/produit sans benchmark ni résultats chiffrés, souvent bruit informationnel."

    return important, ignore


def build_actions(topic_title: str, items: list[FeedItem]) -> list[str]:
    corpus = " ".join((f"{item.title} {item.summary}".lower() for item in items))
    actions: list[str] = []

    if any(term in corpus for term in ("forecast", "prediction", "demand")):
        actions.append(
            "Tester un mini-POC de prévision de la demande (historique + variables exogènes), puis comparer MAPE vs baseline actuelle."
        )
    if any(term in corpus for term in ("last mile", "route", "delivery", "transport")):
        actions.append(
            "Lancer un test d'optimisation de tournées sur un périmètre pilote et mesurer coût/km, taux de service et émissions."
        )
    if any(term in corpus for term in ("robot", "automation", "warehouse", "manufacturing")):
        actions.append(
            "Prioriser un poste candidat à l'automatisation et définir un cadrage ROI: OEE, incidents sécurité, temps de cycle."
        )

    if not actions:
        actions.append(
            f"Construire un backlog de 3 expérimentations data sur « {topic_title} » avec hypothèse, métrique, et critère de décision."
        )
    if len(actions) == 1:
        actions.append(
            "Mettre en place un tableau de bord hebdo (coût, délai, qualité, service) pour objectiver l'impact avant généralisation."
        )

    return actions[:2]


def format_item_datetime(dt: datetime, tz_name: str) -> str:
    if dt.year <= 1970:
        return "Date non fournie"
    tz = safe_timezone(tz_name)
    local_dt = dt.astimezone(tz)
    return local_dt.strftime("%Y-%m-%d %H:%M %Z")


def render_html_email(
    topic_title: str,
    run_date: date,
    items: list[FeedItem],
    signal: str,
    noise: str,
    actions: list[str],
    timezone_name: str,
) -> str:
    item_cards = []
    for item in items:
        card = f"""
        <article class="card">
          <h3>{escape(item.title)}</h3>
          <p class="meta"><strong>Source:</strong> {escape(item.source)} · <strong>Date:</strong> {escape(format_item_datetime(item.published, timezone_name))}</p>
          <p>{escape(item.summary)}</p>
          <p><a href="{escape(item.link)}" target="_blank" rel="noopener noreferrer">Lire l'article</a></p>
        </article>
        """
        item_cards.append(card.strip())

    actions_html = "".join(f"<li>{escape(action)}</li>" for action in actions)
    items_html = "\n".join(item_cards)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Veille {escape(topic_title)} - {run_date.isoformat()}</title>
  <style>
    :root {{
      --bg: #f3f7fb;
      --panel: #ffffff;
      --text: #1b2838;
      --muted: #5b6b7f;
      --accent: #005f99;
      --accent-soft: #d9ecfa;
      --border: #d6e2ef;
    }}
    body {{
      margin: 0;
      padding: 0;
      background: linear-gradient(180deg, #f7fbff 0%, #edf4fb 100%);
      color: var(--text);
      font-family: "Trebuchet MS", "Segoe UI", Arial, sans-serif;
      line-height: 1.55;
    }}
    .container {{
      max-width: 760px;
      margin: 0 auto;
      padding: 24px 14px 40px;
    }}
    .header {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 8px 30px rgba(0, 68, 109, 0.08);
    }}
    .kicker {{
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin: 0 0 6px;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      color: #093b5d;
    }}
    .section {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      margin-top: 16px;
      padding: 16px;
    }}
    .section h2 {{
      margin-top: 0;
      font-size: 18px;
      color: #0a4f7d;
    }}
    .card {{
      border: 1px solid var(--border);
      border-left: 5px solid var(--accent);
      border-radius: 12px;
      padding: 14px;
      margin-bottom: 12px;
      background: #ffffff;
    }}
    .card h3 {{
      margin: 0 0 8px;
      font-size: 17px;
      color: #143247;
    }}
    .meta {{
      margin: 0 0 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    a {{
      color: var(--accent);
      font-weight: 600;
      text-decoration: none;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin-bottom: 8px;
    }}
    .pill {{
      display: inline-block;
      margin-top: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: #0f4c73;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
    }}
    @media (max-width: 600px) {{
      .container {{
        padding: 14px 8px 24px;
      }}
      h1 {{
        font-size: 21px;
      }}
      .section, .header {{
        padding: 14px;
      }}
      .card h3 {{
        font-size: 16px;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <section class="header">
      <p class="kicker">Veille quotidienne</p>
      <h1>{escape(topic_title)} · {run_date.isoformat()}</h1>
      <span class="pill">{len(items)} item(s) sélectionné(s)</span>
    </section>

    <section class="section">
      <h2>Résumé des signaux</h2>
      {items_html}
    </section>

    <section class="section">
      <h2>Signal vs Bruit</h2>
      <ul>
        <li><strong>Pourquoi c'est important:</strong> {escape(signal)}</li>
        <li><strong>À ignorer:</strong> {escape(noise)}</li>
      </ul>
    </section>

    <section class="section">
      <h2>Action</h2>
      <ul>
        {actions_html}
      </ul>
    </section>
  </div>
</body>
</html>
"""


def render_text_email(
    topic_title: str,
    run_date: date,
    items: list[FeedItem],
    signal: str,
    noise: str,
    actions: list[str],
    timezone_name: str,
) -> str:
    lines: list[str] = [
        f"[Veille] {topic_title} - {run_date.isoformat()}",
        "",
        "Signal vs Bruit",
        f"- Pourquoi c'est important: {signal}",
        f"- À ignorer: {noise}",
        "",
        "Action",
    ]
    lines.extend(f"- {action}" for action in actions)
    lines.append("")
    lines.append("Items")

    for idx, item in enumerate(items, start=1):
        lines.extend(
            [
                f"{idx}. {item.title}",
                f"   Source: {item.source}",
                f"   Date: {format_item_datetime(item.published, timezone_name)}",
                f"   Résumé: {item.summary}",
                f"   Lien: {item.link}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "topic"


def write_dry_run(topic: TopicConfig, run_date: date, html_content: str, text_content: str) -> tuple[Path, Path]:
    slug = slugify(topic.key)
    html_path = OUTBOX_DIR / f"{run_date.isoformat()}_{slug}.html"
    txt_path = OUTBOX_DIR / f"{run_date.isoformat()}_{slug}.txt"
    html_path.write_text(html_content, encoding="utf-8")
    txt_path.write_text(text_content, encoding="utf-8")
    return html_path, txt_path


def read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Variable d'environnement manquante: {name}")
    return value


def parse_recipients(raw: str) -> list[str]:
    recipients = [entry.strip() for entry in raw.split(",") if entry.strip()]
    if not recipients:
        raise ValueError("EMAIL_TO est vide")
    return recipients


def send_smtp_email(subject: str, html_content: str, text_content: str) -> None:
    host = read_required_env("SMTP_HOST")
    port = int(read_required_env("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASS", "").strip()
    email_from = read_required_env("EMAIL_FROM")
    email_to = parse_recipients(read_required_env("EMAIL_TO"))

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = ", ".join(email_to)
    message.set_content(text_content)
    message.add_alternative(html_content, subtype="html")

    use_ssl = os.getenv("SMTP_SSL", "false").strip().lower() in {"1", "true", "yes"}
    use_starttls = os.getenv("SMTP_STARTTLS", "true").strip().lower() in {"1", "true", "yes"}

    if use_ssl:
        with smtplib.SMTP_SSL(host=host, port=port, timeout=30) as server:
            if smtp_user:
                server.login(smtp_user, smtp_pass)
            server.send_message(message)
        return

    with smtplib.SMTP(host=host, port=port, timeout=30) as server:
        if use_starttls:
            server.starttls()
        if smtp_user:
            server.login(smtp_user, smtp_pass)
        server.send_message(message)


def process_topic(
    topic: TopicConfig,
    config: AppConfig,
    run_date: date,
    sent_links: set[str],
    openai_cfg: OpenAIConfig | None,
    dry_run: bool,
    logger: logging.Logger,
) -> int:
    items = collect_topic_items(topic, sent_links, config.max_items, logger)
    if not items:
        logger.info("topic_no_new_items", extra={"topic": topic.key, "date": run_date.isoformat()})
        return 0

    for item in items:
        candidate_text = item.raw_text
        if len(candidate_text) < 180:
            fallback = fetch_article_excerpt(item.link, logger)
            if len(fallback) > len(candidate_text):
                candidate_text = fallback
        local_summary = summarize_local(candidate_text, item.title)
        item.summary = maybe_enhance_summary(item, local_summary, openai_cfg, logger)

    signal, noise = build_signal_vs_noise(items)
    actions = build_actions(topic.title, items)

    subject = f"[Veille] {topic.title} - {run_date.isoformat()}"
    html_content = render_html_email(topic.title, run_date, items, signal, noise, actions, config.timezone)
    text_content = render_text_email(topic.title, run_date, items, signal, noise, actions, config.timezone)

    if dry_run:
        html_path, txt_path = write_dry_run(topic, run_date, html_content, text_content)
        logger.info(
            "dry_run_written",
            extra={"topic": topic.key, "html_path": str(html_path), "txt_path": str(txt_path)},
        )
    else:
        send_smtp_email(subject, html_content, text_content)
        logger.info("email_sent", extra={"topic": topic.key, "subject": subject, "items": len(items)})

    for item in items:
        sent_links.add(item.link)
    return len(items)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv()
    ensure_directories()
    logger = setup_logger()

    try:
        config = load_config(Path(args.config))
        run_date = parse_run_date(args.date_str, config.timezone)
        topics = select_topics(config, args.topic, run_date)
    except Exception as exc:
        logger.error("startup_failed", extra={"error": str(exc)})
        return 1

    sent_links = load_state(STATE_FILE, logger)
    if not topics:
        save_state(STATE_FILE, sent_links)
        logger.info("no_topic_scheduled", extra={"date": run_date.isoformat()})
        return 0

    openai_cfg = load_openai_config()
    total_items = 0
    errors = 0

    for topic in topics:
        try:
            logger.info("topic_start", extra={"topic": topic.key, "date": run_date.isoformat(), "dry_run": args.dry_run})
            item_count = process_topic(
                topic=topic,
                config=config,
                run_date=run_date,
                sent_links=sent_links,
                openai_cfg=openai_cfg,
                dry_run=args.dry_run,
                logger=logger,
            )
            total_items += item_count
        except Exception:
            errors += 1
            logger.exception("topic_failed", extra={"topic": topic.key})

    save_state(STATE_FILE, sent_links)
    logger.info(
        "run_complete",
        extra={
            "date": run_date.isoformat(),
            "topics": len(topics),
            "total_items": total_items,
            "errors": errors,
            "dry_run": args.dry_run,
        },
    )
    return 1 if errors == len(topics) and len(topics) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(run())
