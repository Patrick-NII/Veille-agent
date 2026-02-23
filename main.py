#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from src.curate import curate_links, health_summary
from src.dedupe import load_state, save_state
from src.editorial import build_editorial_model, model_to_dict
from src.emailer import parse_recipients_from_env, send_email, write_dry_run
from src.qa import enforce_quality_or_fallback
from src.render import render_email
from src.utils import (
    LOGO_FILE,
    OUTBOX_DIR,
    SOCIAL_ASSETS,
    SOURCES_FILE,
    STATE_FILE,
    TEMPLATE_FILE,
    ensure_directories,
    load_config,
    load_environment,
    now_in_tz,
    parse_args,
    parse_run_date,
    select_topics,
    setup_logger,
    slugify,
)
from src.visuals import generate_simple_diagram, mini_diagram_text


def run() -> int:
    args = parse_args()
    ensure_directories()
    logger = setup_logger()
    load_environment(logger)

    try:
        config = load_config(Path(args.config))
        run_day = parse_run_date(args.run_date, config.timezone)
        topics = select_topics(config, run_day, args.forced_topic)
    except Exception as exc:
        logger.error("Échec du démarrage: %s", exc)
        return 1

    if args.mode == "weekly" and run_day.weekday() != 4 and not args.dry_run:
        logger.info("Mode weekly ignoré: la date %s n'est pas un vendredi", run_day.isoformat())
        return 0

    sent_links = load_state(STATE_FILE)
    if not STATE_FILE.exists():
        save_state(STATE_FILE, sent_links)

    if topics:
        topic = topics[0]
    elif config.topics:
        topic = config.topics[0]
    else:
        logger.error("Aucun topic disponible dans la configuration.")
        return 1

    target_links = 4 if args.mode == "daily" else 5
    curated_links, health = curate_links(
        sources_path=SOURCES_FILE,
        mode=args.mode,
        run_day=run_day,
        sent_links=sent_links,
        logger=logger,
        target_count=target_links,
        fallback_url=config.cta_url,
    )
    logger.info("Sources health | %s", health_summary(health))

    editorial_model = build_editorial_model(
        mode=args.mode,
        run_day=run_day,
        topic_focus=topic.name,
        curated_links=curated_links,
        author_name=config.author_name,
        tagline=config.tagline,
        force_archetype=args.force_archetype,
        topic_hooks=topic.hooks,
    )

    editorial_model, qa_issues = enforce_quality_or_fallback(editorial_model, run_day)
    if qa_issues:
        logger.warning("QA a déclenché le fallback narratif: %s", " | ".join(qa_issues))

    visual_data = {"out_dir": OUTBOX_DIR, "preferred_type": editorial_model.visual_type}
    visual_path = generate_simple_diagram(args.mode, visual_data)
    visual_src = "cid:visual_1" if visual_path is not None else None
    if visual_path is None:
        logger.warning("Génération visuelle indisponible: fallback mini-diagramme texte.")
        editorial_model = replace(
            editorial_model,
            visual_text_fallback=mini_diagram_text(
                editorial_model.visual_type, editorial_model.company, editorial_model.decision_type
            ),
        )

    social_urls = {
        "linkedin": config.linkedin_url,
        "twitter": config.twitter_url,
        "medium": config.medium_url,
        "github": config.github_url,
    }
    social_icon_sources = {
        "linkedin": "cid:social_linkedin",
        "twitter": "cid:social_twitter",
        "medium": "cid:social_medium",
        "github": "cid:social_github",
    }

    html_content, text_content = render_email(
        type="daily_use_case" if args.mode == "daily" else "weekly_deep_dive",
        template_path=TEMPLATE_FILE,
        model=editorial_model,
        cta_url=config.cta_url,
        cta_label=config.cta_label,
        unsubscribe_url=config.unsubscribe_url,
        privacy_url=config.privacy_url,
        contact_url=config.contact_url,
        footer_address=config.footer_address,
        social_urls=social_urls,
        social_icon_sources=social_icon_sources,
        visual_src=visual_src,
        logo_src="cid:logo_head",
    )

    subject = f"[Veille] {editorial_model.title} - {run_day.isoformat()}"
    slug = slugify(f"{args.mode}-{topic.name}")

    if args.dry_run:
        html_path, text_path = write_dry_run(OUTBOX_DIR, run_day, slug, html_content, text_content)
        logger.info("Dry-run HTML généré: %s", html_path)
        logger.info("Dry-run TXT généré: %s", text_path)

        if args.golden and args.mode == "daily":
            golden_html = OUTBOX_DIR / "GOLDEN_daily.html"
            golden_json = OUTBOX_DIR / "GOLDEN_daily.json"
            golden_html.write_text(html_content, encoding="utf-8")
            golden_json.write_text(
                json.dumps(model_to_dict(editorial_model), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Golden sample généré: %s et %s", golden_html, golden_json)
        return 0

    inline_assets = {"logo_head": LOGO_FILE}
    inline_assets.update(SOCIAL_ASSETS)
    if visual_path is not None:
        inline_assets["visual_1"] = visual_path

    try:
        send_email(subject, html_content, text_content, inline_assets)
        recipients = parse_recipients_from_env()
        logger.info("Newsletter envoyée à %s destinataire(s): %s", len(recipients), ", ".join(recipients))
    except Exception as exc:
        logger.error("Échec SMTP: %s", exc)
        return 1

    for link in curated_links:
        if not link.is_placeholder:
            sent_links.add(link.url)
    save_state(STATE_FILE, sent_links)

    logger.info(
        "Exécution terminée pour %s à %s (mode=%s)",
        run_day.isoformat(),
        now_in_tz(config.timezone).isoformat(timespec="seconds"),
        args.mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
