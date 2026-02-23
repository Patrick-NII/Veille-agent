from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Europe/Paris"
DEFAULT_MAX_ITEMS = 8
DEFAULT_MODE = "daily"
SUPPORTED_MODES = {"daily", "weekly", "autopsy"}

ENV_FILES = [Path(".env"), Path("secrets/smtp.env"), Path("secrets/openai.env")]
LOG_FILE = Path("logs/veille-agent.log")
STATE_FILE = Path("state.json")
OUTBOX_DIR = Path("outbox")
LOGS_DIR = Path("logs")
TEMPLATE_FILE = Path("templates/email.html")
LOGO_FILE = Path("logo/Logo-Head.png")
SOURCES_FILE = Path("config/sources.yaml")

ASSET_DIR = Path("assets")
SOCIAL_ASSETS: dict[str, Path] = {
    "social_linkedin": ASSET_DIR / "social/linkedin.svg",
    "social_twitter": ASSET_DIR / "social/x.svg",
    "social_medium": ASSET_DIR / "social/medium.svg",
    "social_github": ASSET_DIR / "social/github.svg",
}

DAY_ALIASES = {
    "MON": "Mon",
    "MONDAY": "Mon",
    "LUN": "Mon",
    "LUNDI": "Mon",
    "TUE": "Tue",
    "TUESDAY": "Tue",
    "MAR": "Tue",
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
    name: str
    days: set[str]
    sources: list[str]
    max_items: int
    hooks: list[str]
    enabled: bool = True


@dataclass(frozen=True)
class AppConfig:
    timezone: str
    max_items: int
    tagline: str
    cta_label: str
    cta_url: str
    unsubscribe_url: str
    privacy_url: str
    contact_url: str
    footer_address: str
    linkedin_url: str
    twitter_url: str
    medium_url: str
    github_url: str
    author_name: str
    topics: list[TopicConfig]


@dataclass
class FeedItem:
    title: str
    link: str
    source: str
    published: datetime
    summary: str
    is_placeholder: bool = False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="pAIpers editorial engine")
    parser.add_argument("--dry-run", action="store_true", help="Write HTML/TXT in outbox without sending")
    parser.add_argument("--date", dest="run_date", help="Simulate execution date YYYY-MM-DD")
    parser.add_argument("--topic", dest="forced_topic", help="Force one topic by key or name")
    parser.add_argument("--limit", dest="limit", type=int, help="Override max items per topic")
    parser.add_argument("--mode", dest="mode", default=DEFAULT_MODE, choices=sorted(SUPPORTED_MODES), help="Editorial mode: daily|weekly|autopsy")
    parser.add_argument("--force-archetype", dest="force_archetype", help="Force storytelling archetype")
    parser.add_argument("--golden", action="store_true", help="Generate GOLDEN_daily.* regression files in outbox")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    return parser.parse_args()


def ensure_directories() -> None:
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("veille-agent")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def load_environment(logger: logging.Logger) -> None:
    loaded: list[str] = []
    for env_path in ENV_FILES:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            loaded.append(str(env_path))
    logger.info("Environment loaded from: %s", ", ".join(loaded) if loaded else "none")


def safe_timezone(tz_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def parse_run_date(run_date: str | None, tz_name: str) -> date:
    if run_date:
        return datetime.strptime(run_date, "%Y-%m-%d").date()
    return datetime.now(safe_timezone(tz_name)).date()


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ValueError(f"Config not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid config: root must be a mapping")

    settings = data.get("settings", {})
    if not isinstance(settings, dict):
        raise ValueError("Invalid config: settings must be a mapping")

    topics_raw = data.get("topics", [])
    if isinstance(topics_raw, dict):
        normalized: list[dict[str, Any]] = []
        for key, value in topics_raw.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("key", str(key))
                item.setdefault("name", str(key))
                normalized.append(item)
        topics_raw = normalized

    if not isinstance(topics_raw, list):
        raise ValueError("Invalid config: topics must be a list")

    topics = [parse_topic(topic) for topic in topics_raw] if topics_raw else []

    max_items = clamp_items(int(settings.get("max_items", DEFAULT_MAX_ITEMS)))
    return AppConfig(
        timezone=str(settings.get("timezone", DEFAULT_TIMEZONE)),
        max_items=max_items,
        tagline=str(settings.get("tagline", "Signaux pour décideurs IA")),
        cta_label=str(settings.get("cta_label", "OUVRIR LE DOSSIER STRATÉGIQUE")),
        cta_url=str(settings.get("cta_url", "https://example.com/brief")),
        unsubscribe_url=str(settings.get("unsubscribe_url", "https://example.com/unsubscribe")),
        privacy_url=str(settings.get("privacy_url", "https://example.com/privacy")),
        contact_url=str(settings.get("contact_url", "https://example.com/contact")),
        footer_address=str(settings.get("footer_address", "4019 Waterview Lane, Santa Fe, NM 87500")),
        linkedin_url=str(settings.get("linkedin_url", "https://www.linkedin.com/company/paipers")),
        twitter_url=str(settings.get("twitter_url", "https://x.com/paipers")),
        medium_url=str(settings.get("medium_url", "https://medium.com/@paipers")),
        github_url=str(settings.get("github_url", "https://github.com/Patrick-NII/Veille-agent")),
        author_name=str(settings.get("author_name", "Patrick.nii")),
        topics=topics,
    )


def parse_topic(raw: Any) -> TopicConfig:
    if not isinstance(raw, dict):
        raise ValueError("Invalid topic block: mapping expected")

    key = str(raw.get("key") or raw.get("name") or "topic").strip()
    name = str(raw.get("name") or key).strip()
    days_raw = raw.get("days", [])
    sources_raw = raw.get("sources", [])
    hooks_raw = raw.get("hooks", [])

    if not isinstance(days_raw, list) or not days_raw:
        raise ValueError(f"Invalid topic '{name}': days must be a non-empty list")
    if not isinstance(sources_raw, list) or not sources_raw:
        raise ValueError(f"Invalid topic '{name}': sources must be a non-empty list")
    if hooks_raw is None:
        hooks_raw = []
    if not isinstance(hooks_raw, list):
        raise ValueError(f"Invalid topic '{name}': hooks must be a list")

    days = {normalize_day(day) for day in days_raw}
    sources = [str(source).strip() for source in sources_raw if str(source).strip()]
    if not sources:
        raise ValueError(f"Invalid topic '{name}': no valid source URL")

    max_items = clamp_items(int(raw.get("max_items", DEFAULT_MAX_ITEMS)))
    enabled = bool(raw.get("enabled", True))
    hooks = [str(item).strip() for item in hooks_raw if str(item).strip()]
    return TopicConfig(key=slugify(key), name=name, days=days, sources=sources, max_items=max_items, hooks=hooks, enabled=enabled)


def normalize_day(value: Any) -> str:
    token = "".join(ch for ch in str(value).upper() if ch.isalpha())
    if token in DAY_ALIASES:
        return DAY_ALIASES[token]
    if len(token) >= 3 and token[:3] in DAY_ALIASES:
        return DAY_ALIASES[token[:3]]
    raise ValueError(f"Invalid day value: {value}")


def day_code(value: date) -> str:
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][value.weekday()]


def clamp_items(value: int) -> int:
    return max(5, min(10, value))


def slugify(value: str) -> str:
    token = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    while "--" in token:
        token = token.replace("--", "-")
    return token.strip("-") or "topic"


def select_topics(config: AppConfig, run_day: date, forced_topic: str | None) -> list[TopicConfig]:
    enabled_topics = [topic for topic in config.topics if topic.enabled]

    if forced_topic:
        needle = forced_topic.strip().lower()
        for topic in enabled_topics:
            if topic.key.lower() == needle or topic.name.lower() == needle:
                return [topic]
        raise ValueError(f"Topic not found: {forced_topic}")

    target_day = day_code(run_day)
    return [topic for topic in enabled_topics if target_day in topic.days]


def now_in_tz(tz_name: str) -> datetime:
    return datetime.now(safe_timezone(tz_name))
