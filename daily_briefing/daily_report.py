from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPORTS_DIR = Path("reports")
METRICS_PATH = Path("state/daily_metrics.json")


def _parse_captured_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def calculate_days_open(captured_date: Optional[str]) -> Optional[int]:
    if not captured_date:
        return None
    parsed = _parse_captured_date(captured_date)
    if not parsed:
        return None
    now = datetime.now(timezone.utc)
    return max((now - parsed.astimezone(timezone.utc)).days, 0)


def _load_metrics_history() -> List[Dict[str, Any]]:
    if not METRICS_PATH.exists():
        return []
    try:
        return json.loads(METRICS_PATH.read_text())
    except json.JSONDecodeError:
        return []


def _save_metrics_history(history: List[Dict[str, Any]]) -> None:
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(history[-30:], indent=2, ensure_ascii=True))


def _normalize_action(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = value.strip().lower()
    if v in {"today", "defer", "archive"}:
        return v
    return None


def _truncate(text: Optional[str], limit: int = 90) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _enrich_items_with_days_open(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    enriched: List[Dict[str, Any]] = []
    for item in items:
        cloned = dict(item)
        cloned["days_open"] = calculate_days_open(item.get("captured_date"))
        cloned["captured_dt"] = _parse_captured_date(item.get("captured_date"))
        if not cloned.get("tag"):
            cloned["tag"] = cloned.get("ai_category") or cloned.get("type")
        if not cloned.get("action"):
            cloned["action"] = _normalize_action(cloned.get("ai_action"))
        enriched.append(cloned)
    return enriched


def _merge_unread_analyses(
    unread_items: List[Dict[str, Any]], analyses: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for item, analysis in zip(unread_items, analyses):
        merged_item = dict(item)
        merged_item["tag"] = analysis.get("tag")
        merged_item["action"] = _normalize_action(analysis.get("action"))
        merged_item["ai_summary"] = analysis.get("summary")
        merged.append(merged_item)
    return merged


def generate_dataset_statistics(items: List[Dict[str, Any]]) -> List[str]:
    category_counts = Counter(item.get("tag") for item in items if item.get("tag"))
    source_counts = Counter(item.get("source") for item in items if item.get("source"))
    total = len(items)
    deferred = sum(1 for i in items if _normalize_action(i.get("action")) == "defer")
    deferred_percentage = int(round((deferred / total) * 100)) if total else 0

    observations: List[str] = []
    if category_counts:
        top_category, _ = category_counts.most_common(1)[0]
        observations.append(f"Most saved items are {str(top_category).lower()}s.")
    if source_counts:
        top_source, _ = source_counts.most_common(1)[0]
        observations.append(f"{top_source} is the dominant capture source.")
    observations.append(f"Deferred items represent {deferred_percentage}% of backlog.")
    return observations[:3]


def _generate_weekly_trends(items: List[Dict[str, Any]]) -> List[str]:
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=7)
    prev_week_start = now - timedelta(days=14)

    this_week = [
        i
        for i in items
        if i.get("captured_dt") and i["captured_dt"].astimezone(timezone.utc) >= week_start
    ]
    prev_week = [
        i
        for i in items
        if i.get("captured_dt")
        and prev_week_start <= i["captured_dt"].astimezone(timezone.utc) < week_start
    ]

    this_cat = Counter(i.get("tag") for i in this_week if i.get("tag"))
    prev_cat = Counter(i.get("tag") for i in prev_week if i.get("tag"))
    this_src = Counter(i.get("source") for i in this_week if i.get("source"))

    insights: List[str] = []
    if this_cat:
        top_cat, top_count = this_cat.most_common(1)[0]
        prev_count = prev_cat.get(top_cat, 0)
        if top_count > prev_count:
            insights.append(f"{top_cat} captures increased this week.")
        elif top_count < prev_count:
            insights.append(f"{top_cat} captures decreased this week.")
        else:
            insights.append(f"{top_cat} captures were steady this week.")

    if this_src:
        top_src, _ = this_src.most_common(1)[0]
        insights.append(f"Most new captures came from {top_src}.")

    if len(this_week) > len(prev_week):
        insights.append("Overall capture volume increased vs last week.")
    elif len(this_week) < len(prev_week):
        insights.append("Overall capture volume decreased vs last week.")
    else:
        insights.append("Overall capture volume was stable week over week.")

    return insights[:3]


def _build_top_actions(items: List[Dict[str, Any]]) -> List[str]:
    candidates = [i for i in items if _normalize_action(i.get("action")) == "today"]
    candidates.sort(key=lambda i: i.get("captured_dt") or datetime.max.replace(tzinfo=timezone.utc))
    actions = [_truncate(c.get("title") or "Untitled task") for c in candidates[:3]]
    while len(actions) < 3:
        actions.append("No additional urgent action.")
    return actions


def _build_followups(items: List[Dict[str, Any]]) -> List[str]:
    followups = [
        i
        for i in items
        if (i.get("days_open") is not None and i.get("days_open") >= 7)
        and _normalize_action(i.get("action")) != "archive"
    ]
    followups.sort(key=lambda i: i.get("days_open") or 0, reverse=True)

    return [
        f"{_truncate(item.get('title') or 'Untitled task')} — open {item.get('days_open')} days"
        for item in followups[:3]
    ]


def _build_worth_revisiting(items: List[Dict[str, Any]]) -> List[str]:
    allowed = {"recipe", "article", "idea"}
    blocked_phrases = {
        "gmail forwarding confirmation",
        "security alert",
        "no-reply",
    }

    def is_candidate(item: Dict[str, Any]) -> bool:
        type_or_tag = str(item.get("type") or item.get("tag") or "").lower()
        title = str(item.get("title") or "").strip().lower()
        if not title or len(title) < 5:
            return False
        if any(p in title for p in blocked_phrases):
            return False
        return type_or_tag in allowed and str(item.get("status") or "") != "Unread"

    candidates = [i for i in items if is_candidate(i)]
    recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    recent = [
        i
        for i in candidates
        if i.get("captured_dt") and i["captured_dt"].astimezone(timezone.utc) >= recent_cutoff
    ]
    recent.sort(key=lambda i: i.get("captured_dt") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    older = [i for i in candidates if i not in recent]
    older.sort(key=lambda i: i.get("captured_dt") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    chosen = (recent + older)[:3]
    unique: List[str] = []
    seen = set()
    for item in chosen:
        title = _truncate(item.get("title") or "Untitled backlog item")
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(title)
    return unique[:3]


def _build_plan(top_actions: List[str], followups: List[str], revisiting: List[str]) -> Dict[str, List[str]]:
    morning = [top_actions[0]] if top_actions else ["Triage urgent items."]
    afternoon = [followups[0]] if followups else [top_actions[1] if len(top_actions) > 1 else "Process deferred backlog."]
    later = []
    if len(top_actions) > 2:
        later.append(top_actions[2])
    later.extend(revisiting[:2])
    if not later:
        later = ["Revisit high-value backlog items.", "Clean up deferred captures."]
    return {
        "morning": morning[:1],
        "afternoon": afternoon[:1],
        "later": later[:2],
    }


def _build_daily_narrative(
    unread_count: int,
    analyzed_unread: List[Dict[str, Any]],
    followups: List[str],
    observations: List[str],
) -> str:
    inbox_state = "remains clear" if unread_count == 0 else f"has {unread_count} new unread items"
    reviewed_count = len(analyzed_unread)
    today_actions = sum(1 for i in analyzed_unread if _normalize_action(i.get("action")) == "today")

    theme = observations[0].replace("Most saved items are ", "").rstrip(".") if observations else "mixed backlog themes"
    lingering = followups[0] if followups else "no major lingering follow-ups"

    return (
        f"Today your inbox {inbox_state}, giving you room to focus on execution. "
        f"You reviewed {reviewed_count} unread items, with {today_actions} marked for immediate action. "
        f"The most notable lingering item is {lingering}. "
        f"Backlog themes are centered on {theme}."
    )


def _compose_briefing_subject(
    today: date,
    num_actions: int,
    num_followups: int,
    unread_count: int,
) -> str:
    inbox_status = "clear" if unread_count == 0 else "active"
    return (
        f"Daily Briefing — {today.strftime('%b')} {today.day} | "
        f"{num_actions} actions | {num_followups} follow-ups | inbox {inbox_status}"
    )


def _cap_words(body: str, max_words: int = 400) -> str:
    words = body.split()
    if len(words) <= max_words:
        return body
    return " ".join(words[:max_words]).rstrip() + "\n"


def generate_daily_briefing(
    all_items: List[Dict[str, Any]],
    unread_items: List[Dict[str, Any]],
    analyses: List[Dict[str, Any]],
) -> Tuple[str, str]:
    enriched_all = _enrich_items_with_days_open(all_items)
    enriched_unread = _enrich_items_with_days_open(_merge_unread_analyses(unread_items, analyses))

    top_actions = _build_top_actions(enriched_unread)
    followups = _build_followups(enriched_all)
    observations = generate_dataset_statistics(enriched_all)
    weekly_trends = _generate_weekly_trends(enriched_all)
    revisiting = _build_worth_revisiting(enriched_all)
    plan = _build_plan(top_actions, followups, revisiting)
    narrative = _build_daily_narrative(len(unread_items), enriched_unread, followups, observations)

    history = _load_metrics_history()
    today = datetime.now(timezone.utc).date()
    yesterday_key = (today - timedelta(days=1)).isoformat()
    yesterday = next((h for h in reversed(history) if h.get("date") == yesterday_key), {})

    reviewed_yesterday = int(yesterday.get("reviewed_count", 0))
    archived_yesterday = int(yesterday.get("archived_count", 0))
    deferred_items = sum(1 for i in enriched_all if _normalize_action(i.get("action")) == "defer")

    lines = [
        "## Daily Review Narrative",
        narrative,
        "",
        "## Top Actions Today",
        f"1. {top_actions[0]}",
        f"2. {top_actions[1]}",
        f"3. {top_actions[2]}",
        "",
        "## Follow-ups",
    ]

    if followups:
        lines.extend([f"• {entry}" for entry in followups[:3]])
    else:
        lines.append("• None currently flagged.")

    lines.extend(
        [
            "",
            "## Inbox Status",
            f"Unread items: {len(unread_items)}",
            f"Reviewed items yesterday: {reviewed_yesterday}",
            f"Archived items yesterday: {archived_yesterday}",
            f"Deferred backlog count: {deferred_items}",
            "",
            "## Observations",
        ]
    )
    lines.extend([f"• {obs}" for obs in observations[:3]])

    lines.extend(["", "## Weekly Trends"])
    lines.extend([f"• {trend}" for trend in weekly_trends[:3]])

    lines.extend(["", "## Worth Revisiting"])
    if revisiting:
        lines.extend([f"• {item}" for item in revisiting[:3]])
    else:
        lines.append("• None selected.")

    lines.extend(
        [
            "",
            "## Suggested Plan",
            "",
            "Morning",
            f"• {plan['morning'][0]}",
            "",
            "Afternoon",
            f"• {plan['afternoon'][0]}",
            "",
            "Later This Week",
            f"• {plan['later'][0]}",
            f"• {plan['later'][1] if len(plan['later']) > 1 else 'Revisit deferred items.'}",
        ]
    )

    body = _cap_words("\n".join(lines).strip() + "\n", 400)

    reviewed_today = len(enriched_unread)
    archived_today = sum(1 for i in enriched_unread if _normalize_action(i.get("action")) == "archive")
    history.append(
        {
            "date": today.isoformat(),
            "reviewed_count": reviewed_today,
            "archived_count": archived_today,
        }
    )
    _save_metrics_history(history)

    subject = _compose_briefing_subject(
        today=today,
        num_actions=sum(1 for a in enriched_unread if _normalize_action(a.get("action")) == "today"),
        num_followups=len(followups),
        unread_count=len(unread_items),
    )
    return subject, body


def generate_daily_narrative(
    all_items: List[Dict[str, Any]],
    unread_items: List[Dict[str, Any]],
    analyses: List[Dict[str, Any]],
) -> str:
    _, body = generate_daily_briefing(all_items, unread_items, analyses)
    return body


def save_daily_report(narrative: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"daily_review_{datetime.now().date().isoformat()}.md"
    report_path.write_text(narrative)
    return report_path
