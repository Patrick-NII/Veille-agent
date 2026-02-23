from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Mapping

from src.editorial import EditorialModel


def render_dynamic_block(model: EditorialModel, visual_src: str | None) -> str:
    rows: list[str] = []

    rows.append(_section_title("Arc Narratif"))
    rows.append(_section_title("1) Accroche"))
    rows.append(_hook(model.arc_narratif.accroche))

    rows.append(_separator())
    rows.append(_section_title("2) Le cas"))
    rows.append(_micro_title("2.1 Situation initiale"))
    rows.append(_paragraph(model.arc_narratif.situation_initiale))
    rows.append(_micro_title("2.2 Décision prise"))
    rows.append(_paragraph(model.arc_narratif.decision_prise))
    rows.append(_micro_title("2.3 Workflow avant → après"))
    rows.append(_bullet_block(model.arc_narratif.workflow_avant_apres))
    rows.append(_micro_title("2.4 Résultat observable"))
    rows.append(_paragraph(model.arc_narratif.resultat_observable))
    rows.append(_micro_title("2.5 Où ça a fissuré"))
    rows.append(_paragraph(model.arc_narratif.fissure_risque))
    rows.append(_micro_title("2.6 Question stratégique"))
    rows.append(_paragraph(model.arc_narratif.question_strategique))

    rows.append(_separator())
    rows.append(_section_title("3) pAIpers Decision Grid™"))
    rows.append(
        _labeled_bullets(
            [
                ("Stratégie", model.decision_grid.strategie),
                ("Architecture", model.decision_grid.architecture),
                ("Gouvernance", model.decision_grid.gouvernance),
                ("Économie", model.decision_grid.economie),
                ("Risque", model.decision_grid.risque),
            ]
        )
    )

    rows.append(_separator())
    rows.append(_section_title("4) Liens sélectionnés"))
    rows.extend(_links_rows(model))

    rows.append(_separator())
    rows.append(_section_title("5) Décryptage exécutif"))
    rows.append(_micro_title("Signal"))
    rows.append(_bullet_block(model.decryptage.signal))
    rows.append(_micro_title("Bruit"))
    rows.append(_bullet_block(model.decryptage.bruit))
    rows.append(_micro_title("Action"))
    rows.append(_bullet_block(model.decryptage.action))
    rows.append(_line("Implication budget", model.decryptage.implication_budget))
    rows.append(_line("Alerte risque", model.decryptage.alerte_risque))

    rows.append(_separator())
    rows.append(_section_title("6) Bloc visuel"))
    if visual_src:
        rows.append(_visual_block(visual_src))
    else:
        rows.append(_visual_text_block(model.visual_text_fallback or _default_visual_text(model)))

    return "\n".join(rows)


def render_email_html(
    template_path: Path,
    model: EditorialModel,
    cta_url: str,
    cta_label: str,
    unsubscribe_url: str,
    privacy_url: str,
    contact_url: str,
    footer_address: str,
    social_urls: Mapping[str, str],
    social_icon_sources: Mapping[str, str],
    visual_src: str | None,
    logo_src: str,
) -> str:
    template = template_path.read_text(encoding="utf-8")

    html = template
    replacements = {
        "{{HEADER_KICKER}}": escape(model.kicker),
        "{{HEADER_TITLE}}": escape(model.title),
        "{{HEADER_SUBTITLE}}": escape(model.subtitle),
        "{{HEADER_AUTHOR}}": escape(model.author_line),
        "{{HEADER_DATE}}": escape(model.date_line),
        "{{DYNAMIC_BLOCK}}": render_dynamic_block(model, visual_src),
        "{{CTA_URL}}": escape(cta_url, quote=True),
        "{{CTA_LABEL}}": escape(cta_label),
        "{{UNSUB_URL}}": escape(unsubscribe_url, quote=True),
        "{{PRIVACY_URL}}": escape(privacy_url, quote=True),
        "{{CONTACT_URL}}": escape(contact_url, quote=True),
        "{{FOOTER_ADDRESS}}": escape(footer_address),
        "{{LINKEDIN_URL}}": escape(social_urls.get("linkedin", "#"), quote=True),
        "{{TWITTER_URL}}": escape(social_urls.get("twitter", "#"), quote=True),
        "{{MEDIUM_URL}}": escape(social_urls.get("medium", "#"), quote=True),
        "{{GITHUB_URL}}": escape(social_urls.get("github", "#"), quote=True),
        "{{LINKEDIN_ICON_SRC}}": escape(social_icon_sources.get("linkedin", ""), quote=True),
        "{{TWITTER_ICON_SRC}}": escape(social_icon_sources.get("twitter", ""), quote=True),
        "{{MEDIUM_ICON_SRC}}": escape(social_icon_sources.get("medium", ""), quote=True),
        "{{GITHUB_ICON_SRC}}": escape(social_icon_sources.get("github", ""), quote=True),
    }

    for key, value in replacements.items():
        html = html.replace(key, value)

    return html.replace("cid:logo_head", escape(logo_src, quote=True), 1)


def render_email_text(model: EditorialModel) -> str:
    lines: list[str] = [
        model.kicker,
        model.title,
        model.subtitle,
        model.author_line,
        model.date_line,
        "",
        "Arc Narratif",
        "Accroche",
        model.arc_narratif.accroche,
        "",
        "Le cas",
        f"Situation initiale: {model.arc_narratif.situation_initiale}",
        f"Décision prise: {model.arc_narratif.decision_prise}",
        "Workflow avant -> après:",
    ]

    lines.extend(f"- {item}" for item in model.arc_narratif.workflow_avant_apres)
    lines.extend(
        [
            f"Résultat observable: {model.arc_narratif.resultat_observable}",
            f"Où ça a fissuré: {model.arc_narratif.fissure_risque}",
            f"Question stratégique: {model.arc_narratif.question_strategique}",
            "",
            "pAIpers Decision Grid",
            f"- Stratégie: {model.decision_grid.strategie}",
            f"- Architecture: {model.decision_grid.architecture}",
            f"- Gouvernance: {model.decision_grid.gouvernance}",
            f"- Économie: {model.decision_grid.economie}",
            f"- Risque: {model.decision_grid.risque}",
            "",
            "Liens sélectionnés",
        ]
    )

    for item in model.links:
        lines.append(f"- {item.title}")
        lines.append(f"  {item.source} • {_format_date(item.published)}")
        lines.append(f"  {item.pourquoi_important}")
        lines.append(f"  {item.url}")

    lines.extend(
        [
            "",
            "Décryptage exécutif",
            "Signal",
        ]
    )
    lines.extend(f"- {value}" for value in model.decryptage.signal)
    lines.append("Bruit")
    lines.extend(f"- {value}" for value in model.decryptage.bruit)
    lines.append("Action")
    lines.extend(f"- {value}" for value in model.decryptage.action)
    lines.append(f"- Implication budget: {model.decryptage.implication_budget}")
    lines.append(f"- Alerte risque: {model.decryptage.alerte_risque}")
    lines.append("")
    return "\n".join(lines)


def render_email(
    *,
    type: str,
    template_path: Path,
    model: EditorialModel,
    cta_url: str,
    cta_label: str,
    unsubscribe_url: str,
    privacy_url: str,
    contact_url: str,
    footer_address: str,
    social_urls: Mapping[str, str],
    social_icon_sources: Mapping[str, str],
    visual_src: str | None,
    logo_src: str,
) -> tuple[str, str]:
    _ = type
    html = render_email_html(
        template_path=template_path,
        model=model,
        cta_url=cta_url,
        cta_label=cta_label,
        unsubscribe_url=unsubscribe_url,
        privacy_url=privacy_url,
        contact_url=contact_url,
        footer_address=footer_address,
        social_urls=social_urls,
        social_icon_sources=social_icon_sources,
        visual_src=visual_src,
        logo_src=logo_src,
    )
    text = render_email_text(model)
    return html, text


def _section_title(value: str) -> str:
    return (
        '<tr><td align="center" style="padding:14px 36px 6px 36px;">'
        f'<h2 style="margin:0; font-family:Arial, Helvetica, sans-serif; font-size:14px; line-height:20px; color:#171717; font-weight:700; text-align:left;">{escape(value)}</h2>'
        "</td></tr>"
    )


def _micro_title(value: str) -> str:
    return (
        '<tr><td align="center" style="padding:8px 42px 2px 42px;">'
        f'<div style="margin:0; text-align:left; font-family:Arial, Helvetica, sans-serif; font-size:12px; line-height:16px; color:#4b4b4b; font-weight:700; letter-spacing:1.2px; text-transform:uppercase;">{escape(value)}</div>'
        "</td></tr>"
    )


def _hook(value: str) -> str:
    return (
        '<tr><td align="center" style="padding:2px 42px 6px 42px;">'
        f'<div style="font-family:Arial, Helvetica, sans-serif; font-size:16px; line-height:22px; color:#121212; font-weight:700; text-align:left;">{escape(value)}</div>'
        "</td></tr>"
    )


def _paragraph(value: str) -> str:
    return (
        '<tr><td align="center" style="padding:0 42px 2px 42px;">'
        f'<div style="font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:20px; color:#2a2a2a; text-align:left;">{escape(value)}</div>'
        "</td></tr>"
    )


def _line(label: str, value: str) -> str:
    return (
        '<tr><td align="center" style="padding:3px 42px 2px 42px;">'
        '<div style="font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:20px; color:#2a2a2a; text-align:left;">'
        f"<strong>{escape(label)} :</strong> {escape(value)}"
        "</div></td></tr>"
    )


def _bullet_block(items: list[str]) -> str:
    bullets = "".join(
        '<tr><td align="left" style="padding:0 0 6px 0;">'
        f'<span style="font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:20px; color:#2a2a2a;">• {escape(item)}</span>'
        "</td></tr>"
        for item in items
    )
    return (
        '<tr><td align="center" style="padding:0 42px 2px 42px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        f"{bullets}"
        "</table></td></tr>"
    )


def _labeled_bullets(items: list[tuple[str, str]]) -> str:
    bullets = "".join(
        '<tr><td align="left" style="padding:0 0 6px 0;">'
        f'<span style="font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:20px; color:#2a2a2a;">• <strong>{escape(label)} :</strong> {escape(value)}</span>'
        "</td></tr>"
        for label, value in items
    )
    return (
        '<tr><td align="center" style="padding:0 42px 2px 42px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        f"{bullets}"
        "</table></td></tr>"
    )


def _links_rows(model: EditorialModel) -> list[str]:
    rows: list[str] = []
    for item in model.links:
        rows.append(
            '<tr><td align="center" style="padding:5px 34px 5px 34px;">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border:1px solid #e9e9e9;">'
            '<tr><td align="left" style="padding:10px 12px 10px 12px;">'
            f'<div style="font-family:Arial, Helvetica, sans-serif; font-size:14px; line-height:20px; font-weight:700;"><a href="{escape(item.url, quote=True)}" style="color:#111111; text-decoration:underline;">{escape(item.title)}</a></div>'
            f'<div style="padding-top:3px; font-family:Arial, Helvetica, sans-serif; font-size:11px; line-height:16px; color:#5c5c5c;">{escape(item.source)} • {escape(_format_date(item.published))}</div>'
            f'<div style="padding-top:6px; font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:18px; color:#2a2a2a;"><strong>Pourquoi c&apos;est important :</strong> {escape(_strip_reason_prefix(item.pourquoi_important))}</div>'
            "</td></tr></table></td></tr>"
        )
    return rows


def _visual_block(src: str) -> str:
    return (
        '<tr><td align="center" style="padding:8px 20px 12px 20px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border:1px solid #e6e6e6; background:#ffffff;">'
        '<tr><td align="center" style="padding:10px 10px 8px 10px;">'
        f'<img src="{escape(src, quote=True)}" alt="Diagramme de décision" width="520" style="display:block; width:100%; max-width:520px; height:auto; border:0;" />'
        "</td></tr></table></td></tr>"
    )


def _visual_text_block(text: str) -> str:
    return (
        '<tr><td align="center" style="padding:8px 20px 12px 20px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border:1px solid #e6e6e6; background:#ffffff;">'
        '<tr><td align="left" style="padding:10px 12px 10px 12px;">'
        f'<pre style="margin:0; font-family:Courier, monospace; font-size:12px; line-height:18px; color:#202020; white-space:pre-wrap;">{escape(text)}</pre>'
        "</td></tr></table></td></tr>"
    )


def _separator() -> str:
    return (
        '<tr><td align="center" style="padding:12px 42px 6px 42px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        '<tr><td style="border-top:1px solid #e8e8e8; font-size:0; line-height:0;">&nbsp;</td></tr>'
        "</table></td></tr>"
    )


def _strip_reason_prefix(value: str) -> str:
    text = value.strip()
    for prefix in (
        "Pourquoi c'est important :",
        "Pourquoi c'est important:",
        "Pourquoi c’est important :",
        "Pourquoi c’est important:",
    ):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text


def _format_date(value: datetime) -> str:
    if value.year <= 1970:
        return "Date indisponible"
    return value.strftime("%Y-%m-%d")


def _default_visual_text(model: EditorialModel) -> str:
    return (
        "AVANT  -> Collecte manuelle -> Validation tardive -> Décision lente\n"
        "APRES  -> Signal priorisé -> Gate explicite -> Décision traçable\n"
        f"POINT  -> {model.company} sécurise la valeur via {model.decision_type}"
    )
