# Veille RSS quotidienne (email)

Projet Python prêt à exécuter pour envoyer chaque jour ouvré une veille thématique par email (ou en `dry-run` HTML).

## Fonctionnalités

- Exécution prévue pour cron (lun-ven).
- Topics configurables dans `config.yaml` avec jours assignés (`Mon`..`Fri`) et sources RSS.
- Déduplication stricte des liens déjà envoyés via `state.json`.
- Sélection de 5 à 15 items max (triés par date décroissante).
- Résumé local heuristique (RSS description + fallback premières phrases de l'article).
- Optionnel: amélioration des résumés via OpenAI si `OPENAI_API_KEY` est défini.
- Double rendu email: HTML moderne responsive + version texte.
- Deux modes de sortie:
  - SMTP (Gmail ou autre serveur SMTP).
  - `--dry-run` vers `outbox/<date>_<topic>.html`.
- Logs structurés JSON dans `logs/veille.log`.

## Arborescence

- `main.py`
- `config.yaml`
- `requirements.txt`
- `README.md`
- `outbox/`
- `logs/`
- `state.json` (créé automatiquement au premier run)

## Setup rapide

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Exemple de `config.yaml`

Le fichier fourni inclut déjà les sources demandées:

- SupplyChainBrain (AI, logistics, last-mile, industrial manufacturing)
- ASSEMBLY (2 flux)
- arXiv (`cs.LG`, `cs.RO`, `eess.SY`)

Vous pouvez ajuster:

- `settings.timezone` (ex: `Europe/Paris`)
- `settings.max_items` (borné automatiquement entre 5 et 15)
- `topics.<topic>.days`
- `topics.<topic>.sources`

## Exemple de `.env`

```dotenv
# SMTP mode
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre_adresse@gmail.com
SMTP_PASS=votre_mot_de_passe_app
EMAIL_FROM=votre_adresse@gmail.com
EMAIL_TO=dest1@entreprise.com,dest2@entreprise.com

# Optionnel
SMTP_STARTTLS=true
SMTP_SSL=false

# Optionnel: amélioration des résumés
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=20
```

## Commandes

### Test local en dry-run

```bash
python main.py --dry-run --date 2026-02-23
```

### Forcer un topic

```bash
python main.py --dry-run --date 2026-02-23 --topic ai_supply_chain
```

### Envoi SMTP (sans `--dry-run`)

```bash
python main.py --date 2026-02-23
```

## Cron (Europe/Paris)

Exemple (lun-ven à 08:15):

```cron
CRON_TZ=Europe/Paris
15 8 * * 1-5 /Users/nii/Documents/Veille-agent/.venv/bin/python /Users/nii/Documents/Veille-agent/main.py >> /Users/nii/Documents/Veille-agent/logs/cron.log 2>&1
```

## Notes de robustesse

- Timeouts réseau et retries simples sur le fetch RSS.
- Gestion d'erreurs par topic: un flux en erreur n'arrête pas tout le run.
- Déduplication par URL canonique (suppression des paramètres de tracking `utm_*`, etc.).
- `state.json` est mis à jour atomiquement (`.tmp` puis replace).
