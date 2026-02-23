from __future__ import annotations

import re
from typing import Mapping

from src.utils import FeedItem

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def summarize_item(item: FeedItem) -> str:
    text = (item.summary or "").strip()
    if not text:
        return _two_line_fallback(item.title)

    sentences = [sentence.strip() for sentence in SENTENCE_SPLIT_RE.split(text) if sentence.strip()]
    if len(sentences) >= 3:
        return " ".join(sentences[:3])
    if len(sentences) == 2:
        return " ".join(sentences)
    if len(sentences) == 1:
        return sentences[0]
    return _two_line_fallback(item.title)


def _two_line_fallback(title: str) -> str:
    return title


def build_signal_noise_action(items_by_topic: Mapping[str, list[FeedItem]]) -> tuple[list[str], list[str], list[str]]:
    corpus = " ".join(
        f"{item.title} {item.summary}".lower()
        for topic_items in items_by_topic.values()
        for item in topic_items
    )

    signal: list[str] = [
        "Les flux montrent des usages IA plus concrets (process, coûts, qualité), donc des opportunités directement pilotables.",
        "Les articles récents accélèrent la convergence entre data science, opérations et exécution terrain.",
    ]
    noise: list[str] = [
        "Écarter les annonces sans métriques terrain (ROI, lead time, taux de service).",
        "Limiter le temps sur les contenus promotionnels qui ne décrivent ni méthode ni résultats.",
    ]
    action: list[str] = [
        "Tester un mini-POC sur un use case prioritaire et comparer à votre baseline actuelle.",
        "Mettre en place un suivi hebdo avec 3 KPI (coût, délai, qualité) avant industrialisation.",
    ]

    if any(word in corpus for word in ("forecast", "demand", "planification", "stock")):
        signal[0] = "Le signal principal est sur la planification et la prévision: impact rapide attendu sur stocks et service."
        action[0] = "Lancer un test de prévision sur un périmètre restreint et suivre MAPE + taux de rupture."

    if any(word in corpus for word in ("robot", "warehouse", "automation", "amr")):
        signal[1] = "La dynamique d'automatisation opérationnelle se confirme, avec gains potentiels en productivité et sécurité."
        action[1] = "Identifier un poste candidat à l'automatisation et cadrer le ROI avec un pilote de 4 semaines."

    if any(word in corpus for word in ("partnership", "launches", "announces", "sponsor")):
        noise[0] = "Bruit dominant: partenariats/annonces produit sans benchmark indépendant ni retour client mesuré."

    return signal[:2], noise[:2], action[:2]
