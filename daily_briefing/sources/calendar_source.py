from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Allow direct script execution: python3 daily_briefing/sources/calendar_source.py
if __package__ is None or __package__ == "":
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2]))

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_service_account_path() -> Path | None:
    if not settings.google_service_account_file:
        return None

    configured_path = Path(settings.google_service_account_file).expanduser()
    if configured_path.is_absolute():
        return configured_path
    return PROJECT_ROOT / configured_path


def _load_calendar_service():
    credentials_path = _resolve_service_account_path()
    if credentials_path is None:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE is not configured.")
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google service account file not found: {credentials_path}"
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(credentials_path),
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=credentials, cache_discovery=False)


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

        try:
            service = _load_calendar_service()
            time_min, time_max = _today_bounds()
            response = (
                service.events()
                .list(
                    calendarId=settings.google_calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except Exception as exc:
            print(f"Skipping Google Calendar events: {exc}")
            return {"calendar_events": []}

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
