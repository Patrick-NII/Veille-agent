from __future__ import annotations

import re

from src.utils import FeedItem

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def summarize_item(item: FeedItem) -> str:
    text = (item.summary or "").strip()
    if not text:
        return item.title

    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(text) if sentence.strip()]
    if len(sentences) >= 3:
        return " ".join(sentences[:3])
    if len(sentences) == 2:
        return " ".join(sentences)
    if len(sentences) == 1:
        return sentences[0]
    return item.title
