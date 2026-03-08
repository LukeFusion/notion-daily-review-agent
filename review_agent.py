from __future__ import annotations

from typing import Any, Dict, List

from daily_report import generate_daily_briefing, save_daily_report
from llm_analysis import analyze_items
from notion_service import build_default_client
from report_delivery import send_report_email
from update_notion import apply_notion_updates


def prepare_notion_updates(
    unread_items: List[Dict[str, Any]], analyses: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    updates: List[Dict[str, Any]] = []
    for item, analysis in zip(unread_items, analyses):
        existing_type = item.get("type")
        inferred_type = analysis.get("tag")
        updates.append(
            {
                "page_id": item.get("id"),
                "status": "Reviewed",
                "type": existing_type or inferred_type,
                "analysis_tag": inferred_type,
                "analysis_action": analysis.get("action"),
                "analysis_summary": analysis.get("summary"),
            }
        )
    return updates


def run() -> None:
    client = build_default_client()
    all_items = client.get_all_items()
    unread_items = [item for item in all_items if item.get("status") == "Unread"]

    print(f"Found {len(all_items)} total item(s).")
    print(f"Found {len(unread_items)} unread item(s).")
    analyses: List[Dict[str, Any]] = []

    if not unread_items:
        print("No unread items to review today.")
    else:
        print("\nUnread item titles:")
        for idx, item in enumerate(unread_items, start=1):
            title = item.get("title") or "(untitled)"
            print(f"{idx}. {title}")

        analyses = analyze_items(unread_items)
        print(f"\nLLM analysis returned {len(analyses)} item(s).")
        if len(analyses) != len(unread_items):
            print(
                "Warning: analysis count does not match unread item count. "
                "Only matched items will be prepared for updates."
            )

        print("\nAnalysis summary:")
        action_counts: Dict[str, int] = {"today": 0, "defer": 0, "archive": 0}
        for analysis in analyses:
            action = analysis.get("action")
            if action in action_counts:
                action_counts[action] += 1
        print(
            "Actions -> "
            f"today: {action_counts['today']}, "
            f"defer: {action_counts['defer']}, "
            f"archive: {action_counts['archive']}"
        )

        updates = prepare_notion_updates(unread_items, analyses)
        print(f"\nPrepared {len(updates)} pending Notion update(s).")

        write_results = apply_notion_updates(updates)
        succeeded = sum(1 for r in write_results if r.get("ok"))
        failed = [r for r in write_results if not r.get("ok")]
        print(f"\nApplied updates in Notion: {succeeded}/{len(write_results)} succeeded.")
        if failed:
            print("\nFailed updates:")
            for result in failed:
                print(f"- page_id: {result.get('page_id')} error: {result.get('error')}")

    subject, narrative = generate_daily_briefing(all_items, unread_items, analyses)
    report_path = save_daily_report(narrative)

    print("\nDaily narrative:")
    print(narrative)
    print(f"\nSaved report: {report_path}")

    sent = send_report_email(
        subject=subject,
        body=narrative,
    )
    if sent:
        print("Report email sent.")
    else:
        print("Report email not sent (SMTP settings not configured).")


if __name__ == "__main__":
    run()
