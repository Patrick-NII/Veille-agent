from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any

from src.curate import CuratedLink
from src.story_builder import StoryPackage, build_story_package


@dataclass(frozen=True)
class ArcNarratif:
    accroche: str
    situation_initiale: str
    decision_prise: str
    workflow_avant_apres: list[str]
    resultat_observable: str
    fissure_risque: str
    question_strategique: str


@dataclass(frozen=True)
class DecisionGrid:
    strategie: str
    architecture: str
    gouvernance: str
    economie: str
    risque: str


@dataclass(frozen=True)
class LinkInsight:
    title: str
    url: str
    source: str
    published: datetime
    pourquoi_important: str
    is_placeholder: bool = False


@dataclass(frozen=True)
class DecryptageExecutif:
    signal: list[str]
    bruit: list[str]
    action: list[str]
    implication_budget: str
    alerte_risque: str


@dataclass(frozen=True)
class EditorialModel:
    mode: str
    topic_focus: str
    kicker: str
    title: str
    subtitle: str
    author_line: str
    date_line: str
    company: str
    sector: str
    decision_type: str
    archetype_name: str
    arc_narratif: ArcNarratif
    decision_grid: DecisionGrid
    links: list[LinkInsight]
    decryptage: DecryptageExecutif
    visual_type: str
    visual_text_fallback: str | None


def build_editorial_model(
    mode: str,
    run_day: date,
    topic_focus: str,
    curated_links: list[CuratedLink],
    author_name: str,
    tagline: str,
    force_archetype: str | None,
    topic_hooks: list[str],
) -> EditorialModel:
    story = build_story_package(
        curated_links=curated_links,
        topic_focus=topic_focus,
        run_day=run_day,
        force_archetype=force_archetype,
        topic_hooks=topic_hooks,
    )
    return _from_story_package(mode, run_day, story, curated_links, author_name, tagline, topic_focus)


def model_to_dict(model: EditorialModel) -> dict[str, Any]:
    payload = asdict(model)
    payload["links"] = [
        {
            "title": item["title"],
            "url": item["url"],
            "source": item["source"],
            "published": item["published"].isoformat() if isinstance(item["published"], datetime) else str(item["published"]),
            "pourquoi_important": item["pourquoi_important"],
            "is_placeholder": item["is_placeholder"],
        }
        for item in payload["links"]
    ]
    return payload


def _from_story_package(
    mode: str,
    run_day: date,
    story: StoryPackage,
    curated_links: list[CuratedLink],
    author_name: str,
    tagline: str,
    topic_focus: str,
) -> EditorialModel:
    title = _headline(story)
    links = _link_block(curated_links, story.link_reasons)
    kicker = _kicker(mode)

    return EditorialModel(
        mode=mode,
        topic_focus=topic_focus,
        kicker=kicker,
        title=title,
        subtitle=tagline,
        author_line=f"Par {author_name}",
        date_line=run_day.isoformat(),
        company=story.company,
        sector=story.sector,
        decision_type=story.decision_type,
        archetype_name=story.archetype_name,
        arc_narratif=ArcNarratif(
            accroche=story.accroche,
            situation_initiale=story.situation_initiale,
            decision_prise=story.decision_prise,
            workflow_avant_apres=story.workflow_avant_apres[:6],
            resultat_observable=story.resultat_observable,
            fissure_risque=story.fissure_risque,
            question_strategique=story.question_strategique,
        ),
        decision_grid=DecisionGrid(
            strategie=story.grid_strategie,
            architecture=story.grid_architecture,
            gouvernance=story.grid_gouvernance,
            economie=story.grid_economie,
            risque=story.grid_risque,
        ),
        links=links,
        decryptage=DecryptageExecutif(
            signal=story.signal[:2],
            bruit=story.bruit[:1],
            action=story.action[:2],
            implication_budget=story.implication_budget,
            alerte_risque=story.alerte_risque,
        ),
        visual_type=story.visual_type,
        visual_text_fallback=None,
    )


def _kicker(mode: str) -> str:
    if mode == "weekly":
        return "pAIpers — Deep Dive Hebdomadaire"
    if mode == "autopsy":
        return "pAIpers — Autopsie Mensuelle"
    return "pAIpers — Brief Quotidien"


def _headline(story: StoryPackage) -> str:
    raw = f"{story.company}: {story.decision_type} pour sécuriser la valeur IA"
    compact = " ".join(raw.split())
    if len(compact) <= 80:
        return compact
    return compact[:79].rstrip() + "…"


def _link_block(curated_links: list[CuratedLink], reasons: list[str]) -> list[LinkInsight]:
    links: list[LinkInsight] = []
    if not curated_links:
        return links

    for idx, link in enumerate(curated_links[:5]):
        reason = reasons[idx] if idx < len(reasons) else "Pourquoi c'est important : ce signal structure la décision du cas."
        links.append(
            LinkInsight(
                title=link.title,
                url=link.url,
                source=link.source,
                published=link.published,
                pourquoi_important=reason,
                is_placeholder=link.is_placeholder,
            )
        )
    return links
