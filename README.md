# veille-agent (MVP)

MVP newsletter engine that builds a daily email brief from RSS sources and sends it via SMTP using a fixed, email-safe HTML template.

## Features

- Fixed template in `/Users/nii/Documents/Veille-agent/templates/email.html` (table-based, Outlook-friendly)
- Dynamic content injected at `{{DYNAMIC_BLOCK}}`
- Inline logo via CID (`logo_head`) in send mode
- Dry-run fallback logo path for HTML preview
- RSS ingest + retries + timeouts
- Deduplication with `/Users/nii/Documents/Veille-agent/state.json`
- Per-topic brief (5-10 items), sorted newest first
- Signal / Noise / Action section
- CLI options: `--dry-run`, `--date`, `--topic`, `--limit`
- Logs in stdout + `/Users/nii/Documents/Veille-agent/logs/veille-agent.log`

## Project structure

- `/Users/nii/Documents/Veille-agent/main.py`
- `/Users/nii/Documents/Veille-agent/config.yaml`
- `/Users/nii/Documents/Veille-agent/templates/email.html`
- `/Users/nii/Documents/Veille-agent/logo/Logo-Head.png`
- `/Users/nii/Documents/Veille-agent/src/fetch.py`
- `/Users/nii/Documents/Veille-agent/src/dedupe.py`
- `/Users/nii/Documents/Veille-agent/src/rank.py`
- `/Users/nii/Documents/Veille-agent/src/summarize.py`
- `/Users/nii/Documents/Veille-agent/src/render.py`
- `/Users/nii/Documents/Veille-agent/src/emailer.py`
- `/Users/nii/Documents/Veille-agent/src/utils.py`
- `/Users/nii/Documents/Veille-agent/scripts/test_smtp.py`
- `/Users/nii/Documents/Veille-agent/outbox/`
- `/Users/nii/Documents/Veille-agent/logs/`

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure `.env`

Use `/Users/nii/Documents/Veille-agent/.env` and `/Users/nii/Documents/Veille-agent/secrets/smtp.env`.

Required SMTP variables:

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASS=app-password
EMAIL_FROM=News Bot <user@example.com>
EMAIL_TO=alice@example.com,bob@example.com
```

Optional transport flags:

```dotenv
SMTP_STARTTLS=true
SMTP_SSL=false
```

- Recommended for port `587`: `SMTP_STARTTLS=true`, `SMTP_SSL=false`
- Recommended for port `465`: `SMTP_STARTTLS=false`, `SMTP_SSL=true`

## Test SMTP only

```bash
python scripts/test_smtp.py
python scripts/test_smtp.py --send-test
```

## Run newsletter (dry-run)

```bash
python main.py --dry-run
python main.py --dry-run --date 2026-02-23
python main.py --dry-run --topic "IA industrielle & logistique"
python main.py --dry-run --limit 6
```

Dry-run writes files in `/Users/nii/Documents/Veille-agent/outbox/`.

## Run newsletter (send)

```bash
python main.py
python main.py --date 2026-02-23
```

## Cron example (Mon-Fri 07:15 Europe/Paris)

```cron
CRON_TZ=Europe/Paris
15 7 * * 1-5 /Users/nii/Documents/Veille-agent/.venv/bin/python /Users/nii/Documents/Veille-agent/main.py >> /Users/nii/Documents/Veille-agent/logs/cron.log 2>&1
```

## Deliverability note (DKIM/SPF)

For reliable inbox placement, configure SPF and DKIM for your sender domain and align `EMAIL_FROM` with that authenticated domain.

## Behavior when feeds fail

If RSS sources are unavailable, the agent injects placeholder content so `--dry-run` still produces at least one HTML preview file.
