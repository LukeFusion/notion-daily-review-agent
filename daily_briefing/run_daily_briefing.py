from __future__ import annotations

# Allow direct script execution: python3 daily_briefing/run_daily_briefing.py
if __package__ is None or __package__ == "":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from daily_briefing.compose_briefing import build_briefing_data
from daily_briefing.daily_report import generate_daily_briefing, save_daily_report
from daily_briefing.report_delivery import send_report_email


def run() -> None:
    data = build_briefing_data()
    all_items = data["all_items"]
    unread_items = data["unread_items"]
    analyses = data["analyses"]

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
        action_counts = {"today": 0, "defer": 0, "archive": 0}
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
