from __future__ import annotations

from src.utils import FeedItem


def rank_items(items: list[FeedItem], limit: int) -> list[FeedItem]:
    ordered = sorted(items, key=lambda item: item.published, reverse=True)
    return ordered[:limit]
