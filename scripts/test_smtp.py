#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

ENV_FILES = [Path(".env"), Path("secrets/smtp.env")]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test SMTP connection for veille-agent")
    parser.add_argument("--send-test", action="store_true", help="Also send a real test message")
    return parser.parse_args()


def load_env() -> None:
    for env_file in ENV_FILES:
        if env_file.exists():
            load_dotenv(env_file, override=False)


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def recipients(raw: str) -> list[str]:
    values = [value.strip() for value in raw.split(",") if value.strip()]
    if not values:
        raise ValueError("EMAIL_TO is empty")
    return values


def main() -> int:
    args = parse_args()
    load_env()

    host = required("SMTP_HOST")
    port = int(required("SMTP_PORT"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASS", "").strip()
    sender = required("EMAIL_FROM")
    to_list = recipients(required("EMAIL_TO"))

    use_ssl = os.getenv("SMTP_SSL", "").strip().lower() in {"1", "true", "yes", "on"}
    if not os.getenv("SMTP_SSL", "").strip():
        use_ssl = port == 465

    use_starttls = os.getenv("SMTP_STARTTLS", "").strip().lower() in {"1", "true", "yes", "on"}
    if not os.getenv("SMTP_STARTTLS", "").strip():
        use_starttls = port == 587 and not use_ssl

    if use_ssl:
        server_cm = smtplib.SMTP_SSL(host=host, port=port, timeout=20)
    else:
        server_cm = smtplib.SMTP(host=host, port=port, timeout=20)

    with server_cm as server:
        if use_starttls and not use_ssl:
            server.ehlo()
            server.starttls()
            server.ehlo()
        if user:
            server.login(user, password)

        print("OK: SMTP connection and login succeeded")

        if args.send_test:
            message = EmailMessage()
            message["Subject"] = "Veille-agent SMTP test"
            message["From"] = sender
            message["To"] = ", ".join(to_list)
            message.set_content("SMTP test successful from veille-agent.")
            server.send_message(message)
            print("OK: Test email sent")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
