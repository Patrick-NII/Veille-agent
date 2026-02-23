from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable

from src.clean import clean_text
from src.curate import CuratedLink
from src.story_templates import StoryArchetype, archetypes

GENERIC_COMPANIES = {
    "",
    "ia",
    "n/a",
    "na",
    "entreprise",
    "organisation",
    "société",
    "company",
    "signal",
    "impact",
    "editorial",
    "référence",
}

STOPWORDS = {
    "The",
    "A",
    "An",
    "How",
    "Why",
    "What",
    "When",
    "Inside",
    "With",
    "And",
    "Or",
    "For",
    "In",
    "By",
    "Le",
    "La",
    "Les",
    "Des",
    "Un",
    "Une",
    "Dans",
    "Vers",
    "Sur",
}

COMPANY_RE = re.compile(r"\b([A-Z][A-Za-z0-9&.-]+(?:\s+[A-Z][A-Za-z0-9&.-]+){0,2})\b")

ARCHETYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "deploiement_copilot": ("copilot", "assistant", "agent", "workflow assistant"),
    "build_vs_buy_plateforme": ("build", "buy", "platform", "plateforme", "vendor", "suite"),
    "gouvernance_gating": ("governance", "compliance", "policy", "gate", "audit"),
    "industrialisation_mlops": ("mlops", "deployment", "monitoring", "pipeline", "drift"),
    "contrainte_finops": ("finops", "cost", "budget", "spend", "unit economics"),
    "socle_data_industriel": ("data platform", "data quality", "data foundation", "lakehouse"),
    "gouvernance_securite": ("security", "cyber", "risk control", "privacy", "sensitive"),
    "modernisation_architecture": ("architecture", "modernization", "legacy", "integration"),
}


@dataclass(frozen=True)
class StoryPackage:
    company: str
    sector: str
    archetype_name: str
    decision_type: str
    accroche: str
    situation_initiale: str
    decision_prise: str
    workflow_avant_apres: list[str]
    resultat_observable: str
    fissure_risque: str
    question_strategique: str
    grid_strategie: str
    grid_architecture: str
    grid_gouvernance: str
    grid_economie: str
    grid_risque: str
    signal: list[str]
    bruit: list[str]
    action: list[str]
    implication_budget: str
    alerte_risque: str
    link_reasons: list[str]
    visual_type: str


def available_archetypes() -> list[str]:
    return sorted(archetypes().keys())


def build_story_package(
    curated_links: list[CuratedLink],
    topic_focus: str,
    run_day: date,
    force_archetype: str | None = None,
    topic_hooks: list[str] | None = None,
) -> StoryPackage:
    templates = archetypes()
    anchor = pick_anchor(curated_links)

    anchor_text = f"{anchor.title} {anchor.summary} {anchor.why_it_matters}" if anchor else ""
    company = infer_company(anchor_text, anchor.source if anchor else "")
    archetype = select_archetype(force_archetype, anchor_text, run_day, templates)

    story = _build_from_archetype(
        archetype=archetype,
        company=company,
        sector=topic_focus,
        anchor=anchor,
        curated_links=curated_links,
        topic_hooks=topic_hooks or [],
    )
    return story


def build_safe_placeholder_story(topic_focus: str, run_day: date, archetype_name: str = "gouvernance_gating") -> StoryPackage:
    templates = archetypes()
    template = templates.get(archetype_name, templates["gouvernance_gating"])
    anchor = CuratedLink(
        title="Cas de référence interne pAIpers",
        url="https://www.paipers.tech/briefs",
        source="pAIpers desk",
        published=_midnight_utc(run_day),
        why_it_matters="Point de repère éditorial.",
        category="Strategy",
        is_placeholder=True,
        summary="",
    )
    return _build_from_archetype(
        archetype=template,
        company="Groupe industriel multi-sites",
        sector=topic_focus,
        anchor=anchor,
        curated_links=[anchor],
        topic_hooks=["Le dossier du jour sert de base de comparaison pour sécuriser les décisions à venir."],
    )


def pick_anchor(curated_links: Iterable[CuratedLink]) -> CuratedLink | None:
    items = list(curated_links)
    if not items:
        return None
    for item in items:
        if not item.is_placeholder:
            return item
    return items[0]


def infer_company(anchor_text: str, source_name: str) -> str:
    candidates = COMPANY_RE.findall(anchor_text)
    for candidate in candidates:
        normalized = candidate.strip()
        first_token = normalized.split()[0] if normalized.split() else normalized
        if first_token in STOPWORDS:
            continue
        if normalized.lower() in GENERIC_COMPANIES:
            continue
        if len(normalized) < 3:
            continue
        return normalized

    source_token = clean_text(source_name).split(" ")
    if source_token and source_token[0]:
        candidate = source_token[0].lower()
        if candidate in {"paipers", "desk"}:
            return "Groupe industriel"
        if candidate not in GENERIC_COMPANIES:
            return source_token[0]
    return "Groupe industriel"


def select_archetype(
    forced: str | None,
    anchor_text: str,
    run_day: date,
    templates: dict[str, StoryArchetype],
) -> StoryArchetype:
    if forced:
        key = forced.strip().lower()
        if key in templates:
            return templates[key]

    lowered = anchor_text.lower()
    for name, keywords in ARCHETYPE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return templates[name]

    ordered = sorted(templates.keys())
    index = run_day.toordinal() % len(ordered)
    return templates[ordered[index]]


def _build_from_archetype(
    archetype: StoryArchetype,
    company: str,
    sector: str,
    anchor: CuratedLink | None,
    curated_links: list[CuratedLink],
    topic_hooks: list[str],
) -> StoryPackage:
    seed_text = f"{company}|{anchor.title if anchor else archetype.name}|{sector}"

    hook = _pick(archetype.hooks, seed_text, 0).format(company=company, sector=sector)
    if topic_hooks:
        hook = f"{clean_text(topic_hooks[0])} {hook}"

    situation = _pick(archetype.situations, seed_text, 1).format(company=company, sector=sector)
    decision = _pick(archetype.decisions, seed_text, 2).format(company=company, sector=sector)
    result = _pick(archetype.outcomes, seed_text, 3).format(company=company, sector=sector)
    risk = _pick(archetype.risks, seed_text, 4).format(company=company, sector=sector)
    question = _pick(archetype.strategic_questions, seed_text, 5).format(company=company, sector=sector)

    workflow_before = [step.format(company=company, sector=sector) for step in archetype.workflow_before]
    workflow_after = [step.format(company=company, sector=sector) for step in archetype.workflow_after]
    workflow = _workflow_bullets(workflow_before, workflow_after)

    link_reasons = [
        _link_reason(company, archetype.decision_label, link, idx)
        for idx, link in enumerate(curated_links[:5])
    ]
    if not link_reasons:
        link_reasons = [
            f"Ce lien sert de repère pour comparer la décision de {company} avec d'autres trajectoires."
        ]

    signal = _distinct_lines(
        [
            _pick(archetype.signal_patterns, seed_text, 6).format(company=company, sector=sector),
            _pick(archetype.signal_patterns, seed_text, 7).format(company=company, sector=sector),
        ],
        fallback=_pick(archetype.signal_patterns, seed_text, 6).format(company=company, sector=sector),
    )
    bruit = [_pick(archetype.noise_patterns, seed_text, 8).format(company=company, sector=sector)]
    action = _distinct_lines(
        [
            _pick(archetype.action_patterns, seed_text, 9).format(company=company, sector=sector),
            _pick(archetype.action_patterns, seed_text, 10).format(company=company, sector=sector),
        ],
        fallback=_pick(archetype.action_patterns, seed_text, 9).format(company=company, sector=sector),
    )

    visual_type = _pick(archetype.visual_types, seed_text, 11)

    return StoryPackage(
        company=clean_text(company),
        sector=clean_text(sector),
        archetype_name=archetype.name,
        decision_type=clean_text(archetype.decision_label),
        accroche=clean_text(_limit_words(hook, 34)),
        situation_initiale=clean_text(_limit_words(situation, 70)),
        decision_prise=clean_text(_limit_words(decision, 70)),
        workflow_avant_apres=workflow[:6],
        resultat_observable=clean_text(_limit_words(result, 60)),
        fissure_risque=clean_text(_limit_words(risk, 70)),
        question_strategique=clean_text(_limit_words(question, 22)),
        grid_strategie=clean_text(_limit_words(archetype.grid_strategy.format(company=company, sector=sector), 18)),
        grid_architecture=clean_text(_limit_words(archetype.grid_architecture.format(company=company, sector=sector), 18)),
        grid_gouvernance=clean_text(_limit_words(archetype.grid_governance.format(company=company, sector=sector), 18)),
        grid_economie=clean_text(_limit_words(archetype.grid_economics.format(company=company, sector=sector), 18)),
        grid_risque=clean_text(_limit_words(archetype.grid_risk.format(company=company, sector=sector), 18)),
        signal=[clean_text(_limit_words(item, 24)) for item in signal[:2]],
        bruit=[clean_text(_limit_words(item, 22)) for item in bruit[:1]],
        action=[clean_text(_limit_words(item, 22)) for item in action[:2]],
        implication_budget=clean_text(_limit_words(archetype.budget_pattern.format(company=company, sector=sector), 20)),
        alerte_risque=clean_text(_limit_words(archetype.risk_alert_pattern.format(company=company, sector=sector), 20)),
        link_reasons=[clean_text(_limit_words(reason, 20)) for reason in link_reasons],
        visual_type=visual_type,
    )


def _workflow_bullets(before: list[str], after: list[str]) -> list[str]:
    bullets: list[str] = []
    for step in before[:3]:
        bullets.append(f"Avant: {clean_text(_limit_words(step, 12))}")
    for step in after[:3]:
        bullets.append(f"Après: {clean_text(_limit_words(step, 12))}")
    return bullets


def _link_reason(company: str, decision_type: str, link: CuratedLink, index: int) -> str:
    title = clean_text(link.title).lower()
    if any(token in title for token in ("cost", "coût", "finops", "budget")):
        return f"Pourquoi c'est important : ce signal affine l'arbitrage budget lié à {decision_type} chez {company}."
    if any(token in title for token in ("governance", "gouvernance", "risk", "compliance", "sécurité")):
        return f"Pourquoi c'est important : ce point éclaire la gouvernance à verrouiller autour de {decision_type}."
    if any(token in title for token in ("platform", "architecture", "mlops", "pipeline", "intégration")):
        return f"Pourquoi c'est important : ce lien précise les contraintes d'architecture du cas {company}."
    if index == 0:
        return f"Pourquoi c'est important : cette source sert d'ancre pour la décision {decision_type} chez {company}."
    return f"Pourquoi c'est important : ce signal aide à comparer des options concrètes autour de {decision_type}."


def _pick(values: list[str], seed_text: str, offset: int) -> str:
    if not values:
        return ""
    index = (abs(hash(f"{seed_text}:{offset}")) % len(values))
    return values[index]


def _limit_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).rstrip(",;:") + "."


def _distinct_lines(values: list[str], fallback: str) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = clean_text(value).lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(clean_text(value))
    while len(lines) < 2:
        candidate = clean_text(fallback)
        if candidate.lower() in seen:
            candidate = f"{candidate} (complément d'exécution)."
        seen.add(candidate.lower())
        lines.append(candidate)
    return lines[:2]


def _midnight_utc(run_day: date):
    from datetime import datetime, timezone

    return datetime(run_day.year, run_day.month, run_day.day, tzinfo=timezone.utc)
