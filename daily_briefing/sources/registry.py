from __future__ import annotations

from typing import List

from daily_briefing.sources.notion_source import NotionSource


def load_sources() -> List[NotionSource]:
    return [
        NotionSource(),
    ]
