from __future__ import annotations

import re
from typing import Any, Dict, List

from notion_client import Client

from config import settings


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _resolve_data_source_id(client: Client, database_id: str) -> str:
    try:
        db = client.databases.retrieve(database_id=database_id)
    except Exception:
        return database_id

    data_sources = db.get("data_sources", [])
    if not data_sources:
        return database_id
    return data_sources[0].get("id", database_id)


def _extract_properties_map(
    data_source: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    properties = data_source.get("properties", {})
    mapped: Dict[str, Dict[str, Any]] = {}

    for key, value in properties.items():
        name = value.get("name") or key
        mapped[name] = {
            "id": value.get("id"),
            "type": value.get("type"),
            "name": name,
        }
    return mapped


def _find_property(
    props: Dict[str, Dict[str, Any]],
    aliases: List[str],
    expected_type: str | None = None,
) -> Dict[str, Any] | None:
    alias_norm = {_normalize(a) for a in aliases}

    for name, meta in props.items():
        if _normalize(name) in alias_norm:
            if expected_type is None or meta.get("type") == expected_type:
                return meta

    for name, meta in props.items():
        normalized = _normalize(name)
        if any(a in normalized for a in alias_norm):
            if expected_type is None or meta.get("type") == expected_type:
                return meta

    return None


def _resolve_property_ids(client: Client) -> Dict[str, str]:
    data_source_id = _resolve_data_source_id(client, settings.notion_database_id)
    data_source = client.data_sources.retrieve(data_source_id=data_source_id)
    props = _extract_properties_map(data_source)

    status = _find_property(props, ["status"], expected_type="select")
    item_type = _find_property(props, ["type"], expected_type="select")
    ai_summary = _find_property(
        props,
        ["ai summary", "summary", "ai notes", "aisummary"],
        expected_type="rich_text",
    )
    ai_category = _find_property(
        props,
        ["ai category", "ai tag", "aicategory", "category"],
        expected_type="select",
    )
    ai_action = _find_property(
        props,
        ["ai action", "action", "next action", "aiaction"],
        expected_type="select",
    )

    missing = []
    if not status:
        missing.append("Status(select)")
    if not item_type:
        missing.append("Type(select)")
    if not ai_summary:
        missing.append("AI Summary(rich_text)")
    if not ai_category:
        missing.append("AI Category(select)")
    if not ai_action:
        missing.append("AI Action(select)")

    if missing:
        available = ", ".join(
            f"{meta['name']}[{meta['type']}]" for meta in props.values()
        )
        raise RuntimeError(
            "Could not map required Notion properties: "
            + ", ".join(missing)
            + f". Available properties: {available}"
        )

    return {
        "status": status["id"],
        "type": item_type["id"],
        "ai_summary": ai_summary["id"],
        "ai_category": ai_category["id"],
        "ai_action": ai_action["id"],
    }


def _rich_text(value: str) -> List[Dict[str, Any]]:
    content = (value or "").strip()
    if len(content) > 1900:
        content = content[:1900]
    return [{"type": "text", "text": {"content": content}}]


def _build_properties(update: Dict[str, Any], prop_ids: Dict[str, str]) -> Dict[str, Any]:
    properties: Dict[str, Any] = {
        prop_ids["status"]: {"select": {"name": "Reviewed"}},
        prop_ids["ai_summary"]: {"rich_text": _rich_text(update.get("analysis_summary", ""))},
        prop_ids["ai_category"]: {"select": {"name": update.get("analysis_tag", "Reference")}},
        prop_ids["ai_action"]: {"select": {"name": update.get("analysis_action", "defer")}},
    }

    # Preserve existing Type when present; otherwise use inferred tag.
    update_type = update.get("type")
    if update_type:
        properties[prop_ids["type"]] = {"select": {"name": update_type}}

    return properties


def apply_notion_updates(updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    client = Client(auth=settings.notion_api_key)
    prop_ids = _resolve_property_ids(client)
    results: List[Dict[str, Any]] = []

    for update in updates:
        page_id = update.get("page_id")
        if not page_id:
            results.append({"page_id": None, "ok": False, "error": "Missing page_id"})
            continue

        try:
            client.pages.update(
                page_id=page_id, properties=_build_properties(update, prop_ids)
            )
            results.append({"page_id": page_id, "ok": True})
        except Exception as exc:
            results.append({"page_id": page_id, "ok": False, "error": str(exc)})

    return results
