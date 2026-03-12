# System Overview

This project contains two independent systems:

1. Notion Engine
2. Daily Briefing Engine

They are intentionally separated so the daily briefing can evolve independently.

---

# Notion Engine

Location:

notion_engine/

Responsibilities:

• read captured items from Notion
• run LLM classification
• update Notion fields
• maintain the Notion database as the system of record

Entry point:

notion_engine/run_notion_updates.py

This system DOES NOT generate reports or send emails.

---

# Daily Briefing Engine

Location:

daily_briefing/

Responsibilities:

• gather information from multiple sources
• generate the daily briefing report
• send the daily email

Entry point:

daily_briefing/run_daily_briefing.py

---

# Briefing Sources

Location:

daily_briefing/sources/

Each source returns structured data used by the daily briefing.

Example sources:

• NotionSource
• WeatherSource
• CalendarSource

All sources follow the pattern:

class Source:
    def fetch(self):
        return {}

---

# Data Flow

Morning automation sequence:

1. Notion Engine runs
2. Notion database updated
3. Daily Briefing Engine runs
4. Briefing reads from sources
5. Email report is generated

---

# Design Principles

• Clear separation of responsibilities
• Notion is the system of record
• Briefing system aggregates data
• Sources should be modular and pluggable