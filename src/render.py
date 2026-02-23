from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Mapping

from src.utils import FeedItem


def render_dynamic_block(
    items_by_topic: Mapping[str, list[FeedItem]],
    signal: list[str],
    noise: list[str],
    action: list[str],
) -> str:
    rows: list[str] = []

    for index, (topic, items) in enumerate(items_by_topic.items()):
        if index > 0:
            rows.append(
                '<tr><td align="center" style="padding:16px 48px 2px 48px;">'
                '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
                '<tr><td style="border-top:1px solid #e8e8e8; font-size:0; line-height:0;">&nbsp;</td></tr>'
                "</table></td></tr>"
            )

        rows.append(
            '<tr><td align="center" style="padding:18px 36px 8px 36px;">'
            f'<div style="font-family:Arial, Helvetica, sans-serif; font-size:19px; line-height:25px; color:#171717; font-weight:700;">{escape(topic)}</div>'
            "</td></tr>"
        )

        for item in items:
            published = _format_date(item.published)
            rows.append(
                '<tr><td align="center" style="padding:6px 34px 6px 34px;">'
                '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
                'style="border:1px solid #eaeaea; border-radius:8px;">'
                '<tr><td align="left" style="padding:12px 14px 12px 14px;">'
                f'<div style="font-family:Arial, Helvetica, sans-serif; font-size:16px; line-height:22px; color:#101010; font-weight:700;">{escape(item.title)}</div>'
                f'<div style="padding-top:4px; font-family:Arial, Helvetica, sans-serif; font-size:11px; line-height:16px; color:#5b5b5b;">{escape(item.source)} • {escape(published)}</div>'
                f'<div style="padding-top:8px; font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:20px; color:#2b2b2b;">{escape(item.summary)}</div>'
                f'<div style="padding-top:10px;"><a href="{escape(item.link, quote=True)}" style="font-family:Arial, Helvetica, sans-serif; font-size:12px; color:#111111; text-decoration:underline;">Lire l\'article</a></div>'
                "</td></tr></table></td></tr>"
            )

    rows.append(
        '<tr><td align="center" style="padding:18px 48px 6px 48px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        '<tr><td style="border-top:1px solid #e8e8e8; font-size:0; line-height:0;">&nbsp;</td></tr>'
        "</table></td></tr>"
    )

    rows.append(_bullet_block("Signal", signal, "#151515"))
    rows.append(_bullet_block("Noise", noise, "#3a3a3a"))
    rows.append(_bullet_block("Action", action, "#151515"))

    return "\n".join(rows)


def render_email_html(
    template_path: Path,
    items_by_topic: Mapping[str, list[FeedItem]],
    signal: list[str],
    noise: list[str],
    action: list[str],
    cta_url: str,
    unsubscribe_url: str,
    privacy_url: str,
    contact_url: str,
    logo_src: str,
) -> str:
    template = template_path.read_text(encoding="utf-8")
    html = template.replace("{{DYNAMIC_BLOCK}}", render_dynamic_block(items_by_topic, signal, noise, action))
    html = html.replace("{{CTA_URL}}", escape(cta_url, quote=True))
    html = html.replace("{{UNSUB_URL}}", escape(unsubscribe_url, quote=True))
    html = html.replace("{{PRIVACY_URL}}", escape(privacy_url, quote=True))
    html = html.replace("{{CONTACT_URL}}", escape(contact_url, quote=True))
    return html.replace("cid:logo_head", escape(logo_src, quote=True), 1)


def render_email_text(
    items_by_topic: Mapping[str, list[FeedItem]],
    signal: list[str],
    noise: list[str],
    action: list[str],
) -> str:
    lines: list[str] = ["pAIpers brief", ""]
    for topic, items in items_by_topic.items():
        lines.append(topic)
        lines.append("-" * len(topic))
        for item in items:
            lines.append(f"• {item.title}")
            lines.append(f"  Source: {item.source}")
            lines.append(f"  Date: {_format_date(item.published)}")
            lines.append(f"  Résumé: {item.summary}")
            lines.append(f"  Lien: {item.link}")
            lines.append("")

    lines.append("Signal")
    lines.extend(f"- {value}" for value in signal)
    lines.append("")
    lines.append("Noise")
    lines.extend(f"- {value}" for value in noise)
    lines.append("")
    lines.append("Action")
    lines.extend(f"- {value}" for value in action)
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def _bullet_block(title: str, values: list[str], color: str) -> str:
    bullets = "".join(
        (
            '<tr><td align="left" style="padding:0 0 6px 0;">'
            f'<span style="font-family:Arial, Helvetica, sans-serif; font-size:13px; line-height:20px; color:#2a2a2a;">• {escape(value)}</span>'
            "</td></tr>"
        )
        for value in values
    )
    return (
        '<tr><td align="center" style="padding:10px 48px 2px 48px;">'
        '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        f'<tr><td align="left" style="padding:0 0 8px 0; font-family:Arial, Helvetica, sans-serif; font-size:14px; line-height:18px; color:{color}; font-weight:700;">{escape(title)}</td></tr>'
        f"{bullets}"
        "</table></td></tr>"
    )


def _format_date(value: datetime) -> str:
    if value.year <= 1970:
        return "Date non fournie"
    return value.strftime("%Y-%m-%d")
