from __future__ import annotations

from typing import Any, Dict, List

from daily_briefing.daily_report import generate_daily_briefing, save_daily_report
from daily_briefing.report_delivery import send_report_email
from notion_engine.run_notion_updates import run_notion_updates


def run() -> None:
    result = run_notion_updates()

    all_items: List[Dict[str, Any]] = result["all_items"]
    unread_items: List[Dict[str, Any]] = result["unread_items"]
    analyses: List[Dict[str, Any]] = result["analyses"]
    updates: List[Dict[str, Any]] = result["updates"]
    write_results: List[Dict[str, Any]] = result["write_results"]

    print(f"Found {len(all_items)} total item(s).")
    print(f"Found {len(unread_items)} unread item(s).")

    if not unread_items:
        print("No unread items to review today.")
    else:
        print("\nUnread item titles:")
        for idx, item in enumerate(unread_items, start=1):
            title = item.get("title") or "(untitled)"
            print(f"{idx}. {title}")

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

        print(f"\nPrepared {len(updates)} pending Notion update(s).")

        succeeded = sum(1 for row in write_results if row.get("ok"))
        failed = [row for row in write_results if not row.get("ok")]
        print(f"\nApplied updates in Notion: {succeeded}/{len(write_results)} succeeded.")
        if failed:
            print("\nFailed updates:")
            for row in failed:
                print(f"- page_id: {row.get('page_id')} error: {row.get('error')}")

    subject, narrative = generate_daily_briefing(
        all_items,
        unread_items,
        analyses,
    )
    report_path = save_daily_report(narrative)

    print("\nDaily narrative:")
    print(narrative)
    print(f"\nSaved report: {report_path}")

    sent = send_report_email(subject=subject, body=narrative)
    if sent:
        print("Report email sent.")
    else:
        print("Report email not sent (SMTP settings not configured).")


if __name__ == "__main__":
    run()
