from __future__ import annotations

import re
from typing import Any, Dict, List

from notion_client import Client

from config import settings


class NotionDailyClient:
    def __init__(self, api_key: str, database_id: str) -> None:
        self.database_id = database_id
        self.client = Client(auth=api_key)
        self.data_source_id = self._resolve_data_source_id()
        self.read_props = self._resolve_read_properties()

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (value or "").lower())

    def _find_property_name(
        self,
        data_source_props: Dict[str, Any],
        aliases: List[str],
        expected_type: str | None = None,
    ) -> str | None:
        alias_norm = {self._normalize(a) for a in aliases}

        for key, meta in data_source_props.items():
            name = meta.get("name") or key
            if self._normalize(name) in alias_norm:
                if expected_type is None or meta.get("type") == expected_type:
                    return name

        for key, meta in data_source_props.items():
            name = meta.get("name") or key
            normalized = self._normalize(name)
            if any(a in normalized for a in alias_norm):
                if expected_type is None or meta.get("type") == expected_type:
                    return name

        return None

    def _resolve_data_source_id(self) -> str:
        """Resolve the first data source id for a database (Notion API v2025+)."""
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
        except Exception:
            # Fallback for environments where the provided id is already a data source id.
            return self.database_id

        data_sources = db.get("data_sources", [])
        if not data_sources:
            return self.database_id
        return data_sources[0].get("id", self.database_id)

    def _resolve_read_properties(self) -> Dict[str, str]:
        try:
            ds = self.client.data_sources.retrieve(data_source_id=self.data_source_id)
            props = ds.get("properties", {})
        except Exception:
            props = {}

        return {
            "title": self._find_property_name(props, ["title"], "title") or "Title",
            "status": self._find_property_name(props, ["status"], "select") or "Status",
            "type": self._find_property_name(props, ["type"], "select") or "Type",
            "source": self._find_property_name(props, ["source"], "select") or "Source",
            "captured_date": self._find_property_name(
                props, ["captured date", "date captured", "captured"], "date"
            )
            or "Captured Date",
            "link": self._find_property_name(props, ["link", "url"], "url") or "Link",
            "raw_content": self._find_property_name(
                props, ["raw content", "content", "notes"], "rich_text"
            )
            or "Raw Content",
            "ai_summary": self._find_property_name(
                props, ["ai summary", "summary", "ai notes"], "rich_text"
            )
            or "AI Summary",
            "ai_category": self._find_property_name(
                props, ["ai category", "ai tag", "category"], "select"
            )
            or "AI Category",
            "ai_action": self._find_property_name(
                props, ["ai action", "action", "next action"], "select"
            )
            or "AI Action",
        }

    def get_all_items(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        next_cursor: str | None = None

        while True:
            query_args: Dict[str, Any] = {"data_source_id": self.data_source_id}
            if next_cursor:
                query_args["start_cursor"] = next_cursor

            response = self.client.data_sources.query(**query_args)
            results = response.get("results", [])
            items.extend(self._parse_row(page) for page in results)

            if not response.get("has_more"):
                break
            next_cursor = response.get("next_cursor")

        return items

    def get_unread_items(self) -> List[Dict[str, Any]]:
        return [item for item in self.get_all_items() if item.get("status") == "Unread"]

    def _parse_row(self, page: Dict[str, Any]) -> Dict[str, Any]:
        props = page.get("properties", {})

        return {
            "id": page.get("id"),
            "title": self._get_title(props, self.read_props["title"]),
            "status": self._get_select(props, self.read_props["status"]),
            "type": self._get_select(props, self.read_props["type"]),
            "source": self._get_select(props, self.read_props["source"]),
            "captured_date": self._get_date(props, self.read_props["captured_date"]),
            "link": self._get_url(props, self.read_props["link"]),
            "raw_content": self._get_rich_text(props, self.read_props["raw_content"]),
            "ai_summary": self._get_rich_text(props, self.read_props["ai_summary"]),
            "ai_category": self._get_select(props, self.read_props["ai_category"]),
            "ai_action": self._get_select(props, self.read_props["ai_action"]),
        }

    @staticmethod
    def _get_title(props: Dict[str, Any], name: str) -> str:
        title_blocks = props.get(name, {}).get("title", [])
        return "".join(block.get("plain_text", "") for block in title_blocks).strip()

    @staticmethod
    def _get_select(props: Dict[str, Any], name: str) -> str | None:
        select_obj = props.get(name, {}).get("select")
        if not select_obj:
            return None
        return select_obj.get("name")

    @staticmethod
    def _get_date(props: Dict[str, Any], name: str) -> str | None:
        date_obj = props.get(name, {}).get("date")
        if not date_obj:
            return None
        return date_obj.get("start")

    @staticmethod
    def _get_url(props: Dict[str, Any], name: str) -> str | None:
        return props.get(name, {}).get("url")

    @staticmethod
    def _get_rich_text(props: Dict[str, Any], name: str) -> str:
        text_blocks = props.get(name, {}).get("rich_text", [])
        return "".join(block.get("plain_text", "") for block in text_blocks).strip()


def build_default_client() -> NotionDailyClient:
    return NotionDailyClient(
        api_key=settings.notion_api_key,
        database_id=settings.notion_database_id,
    )
