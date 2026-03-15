from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _today_bounds() -> tuple[str, str]:
    local_tz = datetime.now().astimezone().tzinfo
    today = date.today()
    start = datetime.combine(today, time.min, tzinfo=local_tz)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


class CalendarSource:
    def fetch(self) -> Dict[str, List[Dict[str, Any]]]:
        if not settings.google_service_account_file:
            return {"calendar_events": []}

        credentials = service_account.Credentials.from_service_account_file(
            settings.google_service_account_file,
            scopes=SCOPES,
        )
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)
        time_min, time_max = _today_bounds()
        response = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events: List[Dict[str, Any]] = []
        for event in response.get("items", []):
            if event.get("status") == "cancelled":
                continue
            start = event.get("start", {})
            end = event.get("end", {})
            events.append(
                {
                    "title": event.get("summary") or "Untitled event",
                    "start": start.get("dateTime") or start.get("date") or "",
                    "end": end.get("dateTime") or end.get("date") or "",
                }
            )

        return {"calendar_events": events}
