from __future__ import annotations

import calendar
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Any

import requests
import yaml

from src.dedupe import canonicalize_url

try:
    import feedparser
except ImportError:  # pragma: no cover
    feedparser = None

REQUEST_TIMEOUT = (3, 8)
MAX_RETRIES = 2
USER_AGENT = "paipers-curate/1.0"
SOURCE_FETCH_BUDGET_SECONDS = 35
MAX_SOURCES_PER_RUN = 12
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class SourceItem:
    category: str
    name: str
    url: str
    placeholder: bool


@dataclass
class CuratedLink:
    title: str
    url: str
    source: str
    published: datetime
    why_it_matters: str
    category: str
    summary: str = ""
    is_placeholder: bool = False


def load_sources(path: Path) -> dict[str, list[SourceItem]]:
    if not path.exists():
        raise ValueError(f"Sources config not found: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid sources config: root mapping expected")

    result: dict[str, list[SourceItem]] = {}
    for category, raw_items in payload.items():
        if not isinstance(raw_items, list):
            continue
        items: list[SourceItem] = []
        for entry in raw_items:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "")).strip()
            url = str(entry.get("url", "")).strip()
            if not name or not url:
                continue
            placeholder = bool(entry.get("placeholder", False)) or "placeholder" in name.lower()
            items.append(SourceItem(category=str(category), name=name, url=url, placeholder=placeholder))
        if items:
            result[str(category)] = items
    return result


def curate_links(
    sources_path: Path,
    mode: str,
    run_day: date,
    sent_links: set[str],
    logger: logging.Logger,
    target_count: int,
    fallback_url: str,
) -> tuple[list[CuratedLink], dict[str, dict[str, int]]]:
    target = max(3, min(5, target_count))

    sources_by_category = load_sources(sources_path)
    priority = _priority_by_day(mode, run_day)

    ordered_categories = sorted(sources_by_category.keys(), key=lambda item: priority.get(item, 99))
    health: dict[str, dict[str, int]] = {
        category: {"ok": 0, "fail": 0, "placeholder": 0, "entries": 0, "skipped": 0}
        for category in ordered_categories
    }

    candidates: list[CuratedLink] = []
    local_seen: set[str] = set()
    started_at = time.monotonic()
    checked_sources = 0
    budget_hit = False

    for category in ordered_categories:
        stats = health[category]
        for source in sources_by_category[category]:
            if checked_sources >= MAX_SOURCES_PER_RUN:
                stats["skipped"] += 1
                continue
            if time.monotonic() - started_at >= SOURCE_FETCH_BUDGET_SECONDS:
                stats["skipped"] += 1
                budget_hit = True
                continue
            if source.placeholder:
                stats["placeholder"] += 1
                continue

            checked_sources += 1
            feed = _fetch_feed(source.url, logger)
            if feed is None:
                stats["fail"] += 1
                continue

            stats["ok"] += 1
            entries = feed.entries if feed.entries else []

            for entry in entries:
                curated = _entry_to_link(entry, source)
                if curated is None:
                    continue
                normalized = canonicalize_url(curated.url)
                if not normalized:
                    continue
                if normalized in sent_links or normalized in local_seen:
                    continue
                curated.url = normalized
                local_seen.add(normalized)
                candidates.append(curated)
                stats["entries"] += 1
                if len(candidates) >= target * 3:
                    break
            if len(candidates) >= target * 3:
                break
        if len(candidates) >= target * 3:
            break

    if budget_hit:
        logger.warning("Source fetch budget reached: %.1fs", SOURCE_FETCH_BUDGET_SECONDS)

    candidates.sort(key=lambda item: (-_to_ts(item.published), priority.get(item.category, 99)))
    selected = candidates[:target]

    if len(selected) < target:
        selected.extend(_placeholder_links(target - len(selected), run_day, fallback_url))

    return selected[:target], health


def health_summary(health: dict[str, dict[str, int]]) -> str:
    parts: list[str] = []
    for category, stats in health.items():
        parts.append(
            f"{category}: ok={stats.get('ok', 0)} fail={stats.get('fail', 0)} "
            f"placeholder={stats.get('placeholder', 0)} entries={stats.get('entries', 0)} "
            f"skipped={stats.get('skipped', 0)}"
        )
    return " | ".join(parts)


def _priority_by_day(mode: str, run_day: date) -> dict[str, int]:
    weekday = run_day.weekday()

    if mode in {"weekly", "autopsy"} or weekday == 4:
        order = ["Strategy", "Enterprise Tech", "MLOps/Architecture", "Industrial/Logistics", "Research"]
    elif weekday in {0, 1}:
        order = ["Strategy", "Enterprise Tech", "Research", "MLOps/Architecture", "Industrial/Logistics"]
    else:
        order = ["Enterprise Tech", "MLOps/Architecture", "Industrial/Logistics", "Strategy", "Research"]

    return {name: index for index, name in enumerate(order)}


def _fetch_feed(url: str, logger: logging.Logger) -> Any | None:
    if feedparser is None:
        logger.error("feedparser missing: run `.venv/bin/python -m pip install -r requirements.txt`")
        return None

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    }
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if getattr(parsed, "bozo", False):
                logger.warning("Feed parse warning [%s]: %s", url, getattr(parsed, "bozo_exception", "unknown"))
            return parsed
        except requests.RequestException as exc:
            logger.warning("Feed request error [%s] attempt %s/%s: %s", url, attempt + 1, MAX_RETRIES + 1, exc)
        except Exception as exc:  # pragma: no cover
            logger.warning("Unexpected feed parsing error [%s] attempt %s/%s: %s", url, attempt + 1, MAX_RETRIES + 1, exc)

    logger.error("Feed failed after retries: %s", url)
    return None


def _entry_to_link(entry: Any, source: SourceItem) -> CuratedLink | None:
    title = str(entry.get("title", "")).strip()
    url = str(entry.get("link", "")).strip()
    if not title or not url:
        return None

    summary = _extract_summary(entry)
    published = _parse_date(entry)

    why = _why_it_matters(title, summary)

    return CuratedLink(
        title=title,
        url=url,
        source=source.name,
        published=published,
        why_it_matters=why,
        category=source.category,
        summary=summary,
        is_placeholder=False,
    )


def _parse_date(entry: Any) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = entry.get(key)
        if parsed:
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)

    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            value = parsedate_to_datetime(str(raw))
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue

    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _extract_summary(entry: Any) -> str:
    for key in ("summary", "description"):
        value = entry.get(key)
        if value:
            return _clean_html(str(value))

    content = entry.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and first.get("value"):
            return _clean_html(str(first["value"]))

    return ""


def _clean_html(value: str) -> str:
    without_tags = TAG_RE.sub(" ", value)
    return SPACE_RE.sub(" ", unescape(without_tags)).strip()


def _why_it_matters(title: str, summary: str) -> str:
    if summary:
        sentence = summary.split(".")[0].strip()
        if sentence:
            short = _trim(sentence, 120)
            return f"Impact décisionnel : {short}"

    lowered = title.lower()
    if any(token in lowered for token in ["governance", "risk", "regulation", "compliance"]):
        return "Impact décisionnel : la posture de gouvernance peut nécessiter un ajustement immédiat."
    if any(token in lowered for token in ["architecture", "platform", "cloud", "mlops"]):
        return "Impact décisionnel : les choix d'architecture conditionnent coût futur et vitesse d'exécution."
    return "Impact décisionnel : signal utile pour la priorisation du portefeuille IA."


def _trim(text: str, max_len: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 1].rstrip() + "…"


def _placeholder_links(count: int, run_day: date, fallback_url: str) -> list[CuratedLink]:
    links: list[CuratedLink] = []
    for idx in range(count):
        links.append(
            CuratedLink(
                title=f"Signal éditorial de référence #{idx + 1}",
                url=fallback_url,
                source="pAIpers desk",
                published=datetime(run_day.year, run_day.month, run_day.day, tzinfo=timezone.utc),
                why_it_matters="Impact décisionnel : maintenir la cadence gouvernance et budget malgré l'instabilité des flux.",
                category="Strategy",
                summary="",
                is_placeholder=True,
            )
        )
    return links


def _to_ts(value: datetime) -> float:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.timestamp()
