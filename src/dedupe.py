from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
}


def load_state(state_path: Path) -> set[str]:
    if not state_path.exists():
        return set()

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()

    sent_links = payload.get("sent_links", [])
    if not isinstance(sent_links, list):
        return set()
    return {str(link) for link in sent_links if isinstance(link, str)}


def save_state(state_path: Path, links: Iterable[str]) -> None:
    unique_links = sorted({link for link in links if link})
    payload = {
        "sent_links": unique_links,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    temp_path = state_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(state_path)


def canonicalize_url(url: str) -> str:
    raw = url.strip()
    if not raw:
        return ""

    parts = urlsplit(raw)
    if not parts.scheme or not parts.netloc:
        return raw

    filtered_query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_KEYS:
            continue
        filtered_query.append((key, value))

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    query = urlencode(filtered_query, doseq=True)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))
