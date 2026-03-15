from __future__ import annotations

from typing import List, Protocol

from daily_briefing.sources.calendar_source import CalendarSource
from daily_briefing.sources.notion_source import NotionSource


class BriefingSource(Protocol):
    def fetch(self) -> dict:
        ...


def load_sources() -> List[BriefingSource]:
    return [
        NotionSource(),
        CalendarSource(),
    ]
