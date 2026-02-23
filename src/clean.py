from __future__ import annotations

import re

MULTI_SPACE_RE = re.compile(r"[ \t]+")
SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,;:.!?])")
MULTI_PUNCT_RE = re.compile(r"([.!?]){2,}")
IKON_NOISE_RE = re.compile(r"(ikon images?|image[s]? credits?).*$", re.IGNORECASE)
DUPLICATED_LABEL_RE = re.compile(
    r"\b(Implication budget|Alerte risque|Signal|Bruit|Action)\s*:\s*\1\s*:\s*",
    re.IGNORECASE,
)


def clean_text(value: str) -> str:
    text = (value or "").strip()
    text = strip_noise_fragments(text)
    text = deduplicate_labels(text)
    text = normalize_spacing(text)
    text = normalize_punctuation(text)
    return text.strip()


def strip_noise_fragments(value: str) -> str:
    text = IKON_NOISE_RE.sub("", value or "")
    return text.strip()


def deduplicate_labels(value: str) -> str:
    text = value or ""
    while True:
        updated = DUPLICATED_LABEL_RE.sub(r"\1 : ", text)
        if updated == text:
            break
        text = updated
    return text.strip()


def normalize_spacing(value: str) -> str:
    text = value or ""
    text = MULTI_SPACE_RE.sub(" ", text)
    text = SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = text.replace("\u00a0", " ")
    return text.strip()


def normalize_punctuation(value: str) -> str:
    text = value or ""
    text = MULTI_PUNCT_RE.sub(r"\1", text)
    text = text.replace(" ,", ",").replace(" .", ".")
    return text.strip()


def split_paragraph_if_long(value: str, max_words: int = 90) -> str:
    words = (value or "").split()
    if len(words) <= max_words:
        return " ".join(words)

    midpoint = min(len(words) - 1, max_words // 2)
    left = " ".join(words[:midpoint]).rstrip(",;:")
    right = " ".join(words[midpoint:]).lstrip(",;:")
    return f"{left}. {right}"


def enforce_short_sentences(value: str, long_sentence_words: int = 24, max_streak: int = 2) -> str:
    text = clean_text(value)
    if not text:
        return text

    sentences = _split_sentences(text)
    if not sentences:
        return text

    streak = 0
    normalized: list[str] = []
    for sentence in sentences:
        count = len(sentence.split())
        if count > long_sentence_words:
            streak += 1
        else:
            streak = 0

        if streak > max_streak:
            sentence = _shorten(sentence, long_sentence_words)
            streak = 1

        normalized.append(sentence)

    return " ".join(normalized).strip()


def _split_sentences(value: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", value.strip())
    return [part.strip() for part in parts if part.strip()]


def _shorten(value: str, words: int) -> str:
    tokens = value.split()
    if len(tokens) <= words:
        return value
    trimmed = " ".join(tokens[:words]).rstrip(",;:")
    if trimmed.endswith((".", "!", "?")):
        return trimmed
    return f"{trimmed}."
