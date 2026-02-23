# pAIpers (veille-agent)

MVP éditorial pour décideurs IA/Data.

Positionnement: **Enterprise AI Orchestration**
(stratégie -> gouvernance -> architecture -> économie -> risque).

Le moteur produit un email HTML **email-client-safe** (tables + styles inline), avec envoi SMTP et mode dry-run.

## Narrative-first

Chaque email applique une règle non négociable: **Arc Narratif**.

Blocs obligatoires:
1. Accroche
2. Situation initiale
3. Décision prise
4. Résultat observable
5. Fissure / Risque émergent + Question stratégique

Si un bloc est vide ou trop générique, la QA déclenche un **fallback narratif cohérent** en français.

## Structure Daily Brief

Le `daily` rend:
1. Accroche
2. Le cas
2.1 Situation initiale
2.2 Décision prise
2.3 Workflow avant -> après
2.4 Résultat observable
2.5 Où ça a fissuré
2.6 Question stratégique
3. pAIpers Decision Grid™
4. Liens sélectionnés (3 à 5)
5. Décryptage exécutif
6. Bloc visuel (CID `visual_1`) ou mini-diagramme texte

Tout le contenu éditorial est en français.

## Weekly / Autopsy

- `weekly`: même pipeline, angle plus approfondi (placeholder MVP).
- `autopsy`: mode autopsie mensuelle (placeholder MVP).

## Architecture

```text
veille-agent/
  main.py
  config.yaml
  config/
    sources.yaml
  templates/
    email.html
  assets/
    social/
  src/
    curate.py
    story_templates.py
    story_builder.py
    clean.py
    qa.py
    editorial.py
    render.py
    visuals.py
    emailer.py
    dedupe.py
    fetch.py
    summarize.py
    utils.py
  scripts/
    test_smtp.py
  outbox/
  logs/
  state.json (auto-créé)
```

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/python -m pip install -r requirements.txt
```

## Configuration

### SMTP (`.env` ou `secrets/smtp.env`)

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASS=app-password
EMAIL_FROM=pAIpers <user@example.com>
EMAIL_TO=alice@example.com,bob@example.com

SMTP_STARTTLS=true
SMTP_SSL=false
```

### `config.yaml`

Contient:
- `author_name`
- `tagline`
- `cta_label`
- liens sociaux
- topics (jours, sources, hooks narratifs optionnels)

### `config/sources.yaml`

Sources de curation par catégories (RSS + placeholders).

## Commandes

### Dry-run

```bash
.venv/bin/python main.py --dry-run --mode daily
.venv/bin/python main.py --dry-run --mode weekly
.venv/bin/python main.py --dry-run --mode autopsy
```

### Archetype forcé

```bash
.venv/bin/python main.py --dry-run --mode daily --force-archetype deploiement_copilot
```

### Golden sample (régression)

```bash
.venv/bin/python main.py --dry-run --mode daily --force-archetype deploiement_copilot --golden
```

Génère:
- `outbox/GOLDEN_daily.html`
- `outbox/GOLDEN_daily.json`

### Envoi SMTP

```bash
.venv/bin/python main.py --mode daily
.venv/bin/python main.py --mode weekly
```

## Template email

Le layout externe reste:
- fond sombre `#232323`
- carte blanche centrée `600px`
- logo en CID `logo_head`
- footer social cliquable (LinkedIn, X, Medium, GitHub)

## Visuals

`src/visuals.py` gère les types:
- `workflow_avant_apres`
- `boucle_feedback`
- `roi_simple`
- `goulot_contrainte`

Si la génération échoue, un mini-diagramme texte est injecté.

## QA / garde-fous

`src/qa.py` et `src/clean.py` appliquent:
- validation stricte de l'Arc Narratif
- nettoyage bruit RSS
- suppression doublons de labels
- contrôle paragraphes longs
- fallback histoire placeholder si nécessaire

## Test SMTP

```bash
.venv/bin/python scripts/test_smtp.py
.venv/bin/python scripts/test_smtp.py --send-test
```

## Cron (Europe/Paris)

Daily (lun-jeu 07:15):

```cron
CRON_TZ=Europe/Paris
15 7 * * 1-4 /Users/nii/Documents/Veille-agent/.venv/bin/python /Users/nii/Documents/Veille-agent/main.py --mode daily >> /Users/nii/Documents/Veille-agent/logs/cron.log 2>&1
```

Weekly (ven 07:15):

```cron
CRON_TZ=Europe/Paris
15 7 * * 5 /Users/nii/Documents/Veille-agent/.venv/bin/python /Users/nii/Documents/Veille-agent/main.py --mode weekly >> /Users/nii/Documents/Veille-agent/logs/cron.log 2>&1
```
