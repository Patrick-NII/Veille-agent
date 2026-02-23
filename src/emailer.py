from __future__ import annotations

import mimetypes
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from typing import Mapping, Sequence


def send_email(
    subject: str,
    html_content: str,
    text_content: str,
    inline_assets: Mapping[str, Path],
) -> None:
    host = _required_env("SMTP_HOST")
    port = int(_required_env("SMTP_PORT"))
    username = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "").strip()
    email_from = _required_env("EMAIL_FROM")
    recipients = _parse_recipients(_required_env("EMAIL_TO"))

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = email_from
    message["To"] = ", ".join(recipients)
    message.set_content(text_content)
    message.add_alternative(html_content, subtype="html")

    html_part = message.get_body(preferencelist=("html",))
    if html_part is not None:
        for cid, file_path in inline_assets.items():
            if not file_path.exists():
                continue
            maintype, subtype = _mime_type(file_path)
            html_part.add_related(file_path.read_bytes(), maintype=maintype, subtype=subtype, cid=f"<{cid}>")

    use_ssl = _bool_env("SMTP_SSL", default=(port == 465))
    use_starttls = _bool_env("SMTP_STARTTLS", default=(port == 587 and not use_ssl))

    if use_ssl:
        with smtplib.SMTP_SSL(host=host, port=port, timeout=30) as server:
            if username:
                server.login(username, password)
            server.send_message(message)
        return

    with smtplib.SMTP(host=host, port=port, timeout=30) as server:
        if use_starttls:
            server.ehlo()
            server.starttls()
            server.ehlo()
        if username:
            server.login(username, password)
        server.send_message(message)


def write_dry_run(
    outbox_dir: Path,
    run_day: date,
    slug: str,
    html_content: str,
    text_content: str,
) -> tuple[Path, Path]:
    html_path = outbox_dir / f"{run_day.isoformat()}_{slug}.html"
    text_path = outbox_dir / f"{run_day.isoformat()}_{slug}.txt"
    html_path.write_text(html_content, encoding="utf-8")
    text_path.write_text(text_content, encoding="utf-8")
    return html_path, text_path


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def _parse_recipients(raw: str) -> list[str]:
    recipients = [entry.strip() for entry in raw.split(",") if entry.strip()]
    if not recipients:
        raise ValueError("EMAIL_TO is empty")
    return recipients


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


def _mime_type(path: Path) -> tuple[str, str]:
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type and "/" in mime_type:
        maintype, subtype = mime_type.split("/", maxsplit=1)
        return maintype, subtype
    return "application", "octet-stream"


def parse_recipients_from_env() -> Sequence[str]:
    return _parse_recipients(_required_env("EMAIL_TO"))
