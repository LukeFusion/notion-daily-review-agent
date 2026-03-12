from __future__ import annotations

from typing import Any, Dict, List

from notion_engine.notion_service import build_default_client


class NotionSource:
    def fetch(self) -> Dict[str, List[Dict[str, Any]]]:
        client = build_default_client()
        all_items = client.get_all_items()
        unread_items = [item for item in all_items if item.get("status") == "Unread"]

        return {
            "all_items": all_items,
            "unread_items": unread_items,
        }
