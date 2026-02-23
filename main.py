#!/usr/bin/env python3
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

from src.dedupe import canonicalize_url, load_state, save_state
from src.emailer import parse_recipients_from_env, send_email, write_dry_run
from src.fetch import fetch_topic_items
from src.rank import rank_items
from src.render import render_email_html, render_email_text
from src.summarize import build_signal_noise_action, summarize_item
from src.utils import (
    LOGO_FILE,
    OUTBOX_DIR,
    STATE_FILE,
    TEMPLATE_FILE,
    FeedItem,
    TopicConfig,
    clamp_items,
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


def build_placeholder(topic: TopicConfig | None, cta_url: str) -> FeedItem:
    title = "Aucun article exploitable aujourd'hui"
    if topic is not None:
        title = f"{topic.name}: aucun article exploitable aujourd'hui"
    return FeedItem(
        title=title,
        link=cta_url,
        source="Veille Agent",
        published=datetime.now(timezone.utc),
        summary=(
            "Les flux RSS sont momentanément indisponibles ou ne contiennent pas de nouveautés non envoyées. "
            "Le template est maintenu pour garantir la continuité de diffusion."
        ),
        is_placeholder=True,
    )


def collect_topic_brief(topic: TopicConfig, sent_links: set[str], limit: int, cta_url: str, logger) -> list[FeedItem]:
    fetched = fetch_topic_items(topic.name, topic.sources, logger)
    deduped: list[FeedItem] = []
    local_seen: set[str] = set()

    for item in fetched:
        normalized_link = canonicalize_url(item.link)
        if not normalized_link:
            continue
        if normalized_link in sent_links or normalized_link in local_seen:
            continue

        local_seen.add(normalized_link)
        item.link = normalized_link
        item.summary = summarize_item(item)
        deduped.append(item)

    ranked = rank_items(deduped, clamp_items(limit))
    if ranked:
        return ranked

    logger.warning("No usable items for topic '%s', injecting placeholder", topic.name)
    return [build_placeholder(topic, cta_url)]


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
        logger.error("Startup failed: %s", exc)
        return 1

    if not topics and not args.dry_run:
        logger.info("No topic scheduled for %s", run_day.isoformat())
        return 0

    sent_links = load_state(STATE_FILE)
    if not STATE_FILE.exists():
        save_state(STATE_FILE, sent_links)
    items_by_topic: OrderedDict[str, list[FeedItem]] = OrderedDict()

    selected_topics = topics
    if not selected_topics and args.dry_run:
        selected_topics = [
            TopicConfig(
                key="preview",
                name="Preview Newsletter",
                days=set(),
                sources=["https://example.com/rss"],
                max_items=5,
                enabled=True,
            )
        ]

    for topic in selected_topics:
        topic_limit = args.limit if args.limit else topic.max_items
        items_by_topic[topic.name] = collect_topic_brief(
            topic=topic,
            sent_links=sent_links,
            limit=topic_limit,
            cta_url=config.cta_url,
            logger=logger,
        )

    if not items_by_topic:
        logger.warning("No content generated")
        return 1

    signal, noise, action = build_signal_noise_action(items_by_topic)

    topic_names = list(items_by_topic.keys())
    subject_topic = topic_names[0] if len(topic_names) == 1 else "Brief quotidien"
    subject = f"[Veille] {subject_topic} - {run_day.isoformat()}"

    logo_src = "cid:logo_head"
    if args.dry_run:
        logo_src = LOGO_FILE.as_posix() if LOGO_FILE.exists() else "https://via.placeholder.com/600x200?text=Logo"

    html_content = render_email_html(
        template_path=TEMPLATE_FILE,
        items_by_topic=items_by_topic,
        signal=signal,
        noise=noise,
        action=action,
        cta_url=config.cta_url,
        unsubscribe_url=config.unsubscribe_url,
        privacy_url=config.privacy_url,
        contact_url=config.contact_url,
        logo_src=logo_src,
    )
    text_content = render_email_text(items_by_topic, signal, noise, action)

    slug_base = slugify(subject_topic if len(topic_names) == 1 else "newsletter")

    if args.dry_run:
        html_path, text_path = write_dry_run(OUTBOX_DIR, run_day, slug_base, html_content, text_content)
        logger.info("Dry-run file generated: %s", html_path)
        logger.info("Dry-run text generated: %s", text_path)
        return 0

    try:
        send_email(subject, html_content, text_content, LOGO_FILE)
        recipients = parse_recipients_from_env()
        logger.info("Newsletter sent to %s recipient(s): %s", len(recipients), ", ".join(recipients))
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return 1

    for topic_items in items_by_topic.values():
        for item in topic_items:
            if not item.is_placeholder:
                sent_links.add(item.link)
    save_state(STATE_FILE, sent_links)

    logger.info(
        "Run complete for %s at %s (%s topics)",
        run_day.isoformat(),
        now_in_tz(config.timezone).isoformat(timespec="seconds"),
        len(topic_names),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
