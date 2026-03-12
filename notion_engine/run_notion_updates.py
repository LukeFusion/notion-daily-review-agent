from __future__ import annotations

from typing import Any, Dict, List

# Allow direct script execution: python3 notion_engine/run_notion_updates.py
if __package__ is None or __package__ == "":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[1]))

from notion_engine.llm_analysis import analyze_items
from notion_engine.notion_service import build_default_client
from notion_engine.update_notion import apply_notion_updates


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


def run_notion_updates() -> Dict[str, Any]:
    client = build_default_client()
    all_items = client.get_all_items()
    unread_items = [item for item in all_items if item.get("status") == "Unread"]

    analyses: List[Dict[str, Any]] = []
    updates: List[Dict[str, Any]] = []
    write_results: List[Dict[str, Any]] = []

    if unread_items:
        analyses = analyze_items(unread_items)
        updates = prepare_notion_updates(unread_items, analyses)
        write_results = apply_notion_updates(updates)

    return {
        "all_items": all_items,
        "unread_items": unread_items,
        "analyses": analyses,
        "updates": updates,
        "write_results": write_results,
    }


def run() -> None:
    result = run_notion_updates()

    all_items = result["all_items"]
    unread_items = result["unread_items"]
    analyses = result["analyses"]
    updates = result["updates"]
    write_results = result["write_results"]

    print(f"Found {len(all_items)} total item(s).")
    print(f"Found {len(unread_items)} unread item(s).")

    if not unread_items:
        print("No unread items to review today.")
        return

    print("\nUnread item titles:")
    for idx, item in enumerate(unread_items, start=1):
        title = item.get("title") or "(untitled)"
        print(f"{idx}. {title}")

    print(f"\nLLM analysis returned {len(analyses)} item(s).")
    if len(analyses) != len(unread_items):
        print(
            "Warning: analysis count does not match unread item count. "
            "Only matched items were prepared for updates."
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

    succeeded = sum(1 for r in write_results if r.get("ok"))
    failed = [r for r in write_results if not r.get("ok")]
    print(f"\nApplied updates in Notion: {succeeded}/{len(write_results)} succeeded.")
    if failed:
        print("\nFailed updates:")
        for row in failed:
            print(f"- page_id: {row.get('page_id')} error: {row.get('error')}")


if __name__ == "__main__":
    run()
