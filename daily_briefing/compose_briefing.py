from __future__ import annotations

from typing import Any, Dict, List

from daily_briefing.sources.registry import load_sources
from notion_engine.llm_analysis import analyze_items


def build_briefing_data() -> Dict[str, List[Dict[str, Any]]]:
    sources = load_sources()
    combined_data: Dict[str, Any] = {}

    for source in sources:
        result = source.fetch()
        combined_data.update(result)

    all_items = combined_data["all_items"]
    unread_items = combined_data["unread_items"]
    analyses = analyze_items(unread_items) if unread_items else []

    return {
        "all_items": all_items,
        "unread_items": unread_items,
        "analyses": analyses,
    }
