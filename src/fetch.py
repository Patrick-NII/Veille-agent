from __future__ import annotations

import calendar
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re

import requests

from src.utils import FeedItem

try:
    import feedparser
except ImportError:  # pragma: no cover
    feedparser = None

REQUEST_TIMEOUT = (3, 8)
MAX_RETRIES = 2
USER_AGENT = "veille-agent-mvp/1.0"
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def fetch_topic_items(topic_name: str, sources: list[str], logger: logging.Logger) -> list[FeedItem]:
    items: list[FeedItem] = []
    for source_url in sources:
        parsed = _fetch_feed(source_url, logger)
        if parsed is None:
            continue

        feed_title = str(parsed.feed.get("title") or topic_name)
        for entry in parsed.entries:
            item = _entry_to_item(entry, feed_title)
            if item is not None:
                items.append(item)

    return items


def _fetch_feed(url: str, logger: logging.Logger):
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
            logger.warning("Unexpected feed parse error [%s] attempt %s/%s: %s", url, attempt + 1, MAX_RETRIES + 1, exc)

    logger.error("Feed failed after retries: %s", url)
    return None


def _entry_to_item(entry, fallback_source: str) -> FeedItem | None:
    title = str(entry.get("title", "")).strip()
    link = str(entry.get("link", "")).strip()
    if not title or not link:
        return None

    source = fallback_source
    source_meta = entry.get("source")
    if isinstance(source_meta, dict):
        source_title = str(source_meta.get("title", "")).strip()
        if source_title:
            source = source_title

    published = _parse_published(entry)
    summary = _extract_summary(entry)

    return FeedItem(
        title=title,
        link=link,
        source=source,
        published=published,
        summary=summary,
        is_placeholder=False,
    )


def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            return datetime.fromtimestamp(calendar.timegm(value), tz=timezone.utc)

    for key in ("published", "updated", "created"):
        raw = entry.get(key)
        if not raw:
            continue
        try:
            dt = parsedate_to_datetime(str(raw))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue

    return datetime(1970, 1, 1, tzinfo=timezone.utc)


def _extract_summary(entry: feedparser.FeedParserDict) -> str:
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
