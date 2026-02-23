from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Iterable

from src.clean import clean_text, enforce_short_sentences, split_paragraph_if_long
from src.editorial import ArcNarratif, DecisionGrid, DecryptageExecutif, EditorialModel
from src.story_builder import build_safe_placeholder_story

FILLER_STARTS = (
    "l’ia en entreprise nécessite",
    "l'ia en entreprise nécessite",
    "ia en entreprise nécessite",
)

GENERIC_COMPANIES = {"", "ia", "n/a", "na", "entreprise", "organisation", "société", "company"}


def enforce_quality_or_fallback(model: EditorialModel, run_day: date) -> tuple[EditorialModel, list[str]]:
    cleaned = clean_editorial_model(model)
    errors = validate_editorial_model(cleaned)
    if not errors:
        return cleaned, []

    safe_story = build_safe_placeholder_story(
        topic_focus=cleaned.topic_focus,
        run_day=run_day,
        archetype_name=cleaned.archetype_name,
    )
    fallback = replace(
        cleaned,
        company=safe_story.company,
        sector=safe_story.sector,
        decision_type=safe_story.decision_type,
        archetype_name=safe_story.archetype_name,
        arc_narratif=ArcNarratif(
            accroche=safe_story.accroche,
            situation_initiale=safe_story.situation_initiale,
            decision_prise=safe_story.decision_prise,
            workflow_avant_apres=safe_story.workflow_avant_apres,
            resultat_observable=safe_story.resultat_observable,
            fissure_risque=safe_story.fissure_risque,
            question_strategique=safe_story.question_strategique,
        ),
        decision_grid=DecisionGrid(
            strategie=safe_story.grid_strategie,
            architecture=safe_story.grid_architecture,
            gouvernance=safe_story.grid_gouvernance,
            economie=safe_story.grid_economie,
            risque=safe_story.grid_risque,
        ),
        decryptage=DecryptageExecutif(
            signal=safe_story.signal[:2],
            bruit=safe_story.bruit[:1],
            action=safe_story.action[:2],
            implication_budget=safe_story.implication_budget,
            alerte_risque=safe_story.alerte_risque,
        ),
        visual_type=safe_story.visual_type,
    )
    return clean_editorial_model(fallback), errors


def clean_editorial_model(model: EditorialModel) -> EditorialModel:
    arc = model.arc_narratif
    cleaned_arc = ArcNarratif(
        accroche=_tidy(arc.accroche, 40),
        situation_initiale=_tidy(arc.situation_initiale, 90),
        decision_prise=_tidy(arc.decision_prise, 90),
        workflow_avant_apres=[_tidy(item, 40) for item in arc.workflow_avant_apres[:6]],
        resultat_observable=_tidy(arc.resultat_observable, 80),
        fissure_risque=_tidy(arc.fissure_risque, 90),
        question_strategique=_tidy(arc.question_strategique, 28),
    )
    grid = model.decision_grid
    cleaned_grid = DecisionGrid(
        strategie=_tidy(grid.strategie, 24),
        architecture=_tidy(grid.architecture, 24),
        gouvernance=_tidy(grid.gouvernance, 24),
        economie=_tidy(grid.economie, 24),
        risque=_tidy(grid.risque, 24),
    )
    decrypt = model.decryptage
    cleaned_decrypt = DecryptageExecutif(
        signal=[_tidy(item, 26) for item in decrypt.signal[:2]],
        bruit=[_tidy(item, 24) for item in decrypt.bruit[:1]],
        action=[_tidy(item, 24) for item in decrypt.action[:2]],
        implication_budget=_tidy(decrypt.implication_budget, 24),
        alerte_risque=_tidy(decrypt.alerte_risque, 24),
    )

    cleaned_links = []
    for item in model.links:
        cleaned_links.append(
            replace(
                item,
                title=_tidy(item.title, 24),
                source=_tidy(item.source, 10),
                pourquoi_important=_tidy(item.pourquoi_important, 28),
            )
        )

    return replace(
        model,
        kicker=_tidy(model.kicker, 12),
        title=_tidy(model.title, 20),
        subtitle=_tidy(model.subtitle, 16),
        author_line=_tidy(model.author_line, 8),
        company=_tidy(model.company, 6),
        sector=_tidy(model.sector, 8),
        decision_type=_tidy(model.decision_type, 8),
        arc_narratif=cleaned_arc,
        decision_grid=cleaned_grid,
        links=cleaned_links,
        decryptage=cleaned_decrypt,
    )


def validate_editorial_model(model: EditorialModel) -> list[str]:
    errors: list[str] = []
    errors.extend(_validate_arc(model.arc_narratif))

    if _is_generic_company(model.company):
        errors.append("Entreprise générique ou vide.")

    filler_fields = {
        "accroche": model.arc_narratif.accroche,
        "situation_initiale": model.arc_narratif.situation_initiale,
        "decision_prise": model.arc_narratif.decision_prise,
        "resultat_observable": model.arc_narratif.resultat_observable,
        "fissure_risque": model.arc_narratif.fissure_risque,
        "question_strategique": model.arc_narratif.question_strategique,
    }
    for name, value in filler_fields.items():
        if _starts_with_filler(value):
            errors.append(f"Section trop générique: {name}")

    if len(model.links) < 3:
        errors.append("Moins de 3 liens sélectionnés.")

    for link in model.links:
        if "Pourquoi c'est important" not in link.pourquoi_important and "Pourquoi c’est important" not in link.pourquoi_important:
            errors.append("Lien sans ligne 'Pourquoi c'est important'.")
            break

    if _has_label_duplications(_collect_text(model)):
        errors.append("Doublon de labels détecté.")

    for field in _collect_text(model):
        if _word_count(field) > 90:
            errors.append("Paragraphe trop long détecté.")
            break

    return errors


def _validate_arc(arc: ArcNarratif) -> list[str]:
    errors: list[str] = []
    blocks = {
        "accroche": arc.accroche,
        "situation_initiale": arc.situation_initiale,
        "decision_prise": arc.decision_prise,
        "resultat_observable": arc.resultat_observable,
        "fissure_risque": arc.fissure_risque,
        "question_strategique": arc.question_strategique,
    }
    for name, value in blocks.items():
        if not value or len(value.split()) < 4:
            errors.append(f"Bloc narratif manquant ou faible: {name}")
        if _looks_generic(value):
            errors.append(f"Bloc narratif trop générique: {name}")
    if len(arc.workflow_avant_apres) < 2:
        errors.append("Workflow avant/après insuffisant.")
    return errors


def _tidy(value: str, max_words: int) -> str:
    text = clean_text(value)
    text = split_paragraph_if_long(text, max_words=90)
    text = enforce_short_sentences(text)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]).rstrip(",;:") + "."
    return text.strip()


def _is_generic_company(value: str) -> bool:
    normalized = clean_text(value).lower()
    return normalized in GENERIC_COMPANIES or len(normalized) < 3


def _looks_generic(value: str) -> bool:
    lowered = clean_text(value).lower()
    return lowered in {"entreprise: ia", "entreprise ia", "n/a", "sans objet", "à définir"} or len(lowered) < 16


def _starts_with_filler(value: str) -> bool:
    lowered = clean_text(value).lower()
    return any(lowered.startswith(prefix) for prefix in FILLER_STARTS)


def _collect_text(model: EditorialModel) -> list[str]:
    values: list[str] = [
        model.title,
        model.subtitle,
        model.company,
        model.sector,
        model.decision_type,
        model.arc_narratif.accroche,
        model.arc_narratif.situation_initiale,
        model.arc_narratif.decision_prise,
        model.arc_narratif.resultat_observable,
        model.arc_narratif.fissure_risque,
        model.arc_narratif.question_strategique,
        model.decision_grid.strategie,
        model.decision_grid.architecture,
        model.decision_grid.gouvernance,
        model.decision_grid.economie,
        model.decision_grid.risque,
        model.decryptage.implication_budget,
        model.decryptage.alerte_risque,
    ]
    values.extend(model.arc_narratif.workflow_avant_apres)
    values.extend(model.decryptage.signal)
    values.extend(model.decryptage.bruit)
    values.extend(model.decryptage.action)
    values.extend(item.pourquoi_important for item in model.links)
    return values


def _word_count(value: str) -> int:
    return len((value or "").split())


def _has_label_duplications(values: Iterable[str]) -> bool:
    for value in values:
        normalized = (value or "").lower()
        if "implication budget : implication budget" in normalized:
            return True
        if "alerte risque : alerte risque" in normalized:
            return True
    return False
