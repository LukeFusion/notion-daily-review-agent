from __future__ import annotations

import json
from typing import Any, Dict, List, Literal

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import settings


ALLOWED_TAGS = ["Recipe", "Article", "Reminder", "Job", "Idea", "To Buy", "Reference"]
ALLOWED_ACTIONS = ["today", "defer", "archive"]


class AnalysisItem(BaseModel):
    title: str
    summary: str
    tag: Literal["Recipe", "Article", "Reminder", "Job", "Idea", "To Buy", "Reference"]
    action: Literal["today", "defer", "archive"]


def _compact_items_for_prompt(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compacted: List[Dict[str, Any]] = []
    for item in items:
        raw_content = (item.get("raw_content") or "").strip()
        compacted.append(
            {
                "title": item.get("title") or "",
                "type": item.get("type"),
                "source": item.get("source"),
                "captured_date": item.get("captured_date"),
                "link": item.get("link"),
                # Cap noisy content to keep prompts bounded.
                "raw_content": raw_content[:1200],
            }
        )
    return compacted


def _parse_analysis_json(content: str) -> List[Dict[str, Any]]:
    parsed = json.loads(content)
    if not isinstance(parsed, list):
        raise ValueError("LLM response must be a JSON array.")

    validated: List[Dict[str, Any]] = []
    for obj in parsed:
        validated_item = AnalysisItem.model_validate(obj)
        validated.append(validated_item.model_dump())
    return validated


def analyze_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not items:
        return []

    client = OpenAI(api_key=settings.openai_api_key)
    compact_items = _compact_items_for_prompt(items)

    system_prompt = (
        "You are a daily review assistant. "
        "Classify each item and return ONLY a JSON array. "
        "Return exactly one output object per input item, in the same order. "
        f"Allowed tags: {', '.join(ALLOWED_TAGS)}. "
        f"Allowed actions: {', '.join(ALLOWED_ACTIONS)}. "
        "Keep summaries concise and practical."
    )

    user_prompt = (
        "Analyze the following items and produce JSON with fields: "
        "title, summary, tag, action.\n\n"
        f"{json.dumps(compact_items, ensure_ascii=True)}"
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content or "[]"
    try:
        return _parse_analysis_json(content)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise RuntimeError(f"Failed to parse LLM analysis output: {exc}") from exc
