# Project Refactor Plan: Separate Notion Automation from Daily Briefing

## Objective

Refactor the current project so that two core responsibilities are clearly separated:

1. **Notion Engine** – responsible only for analyzing and updating the Notion database.
2. **Daily Briefing Engine** – responsible for generating the daily email report using data from multiple sources (Notion, weather, calendar, etc.).

This separation will allow the daily briefing system to evolve independently without complicating the Notion automation logic.

---

# Target Architecture

```
project-root/

notion_engine/
    notion_service.py
    llm_analysis.py
    update_notion.py
    run_notion_updates.py


daily_briefing/
    compose_briefing.py
    daily_report.py
    send_email.py
    run_daily_briefing.py

    sources/
        notion_source.py
        weather_source.py
        calendar_source.py
```

---

# Job Responsibilities

## Job 1 — Notion Engine

Entry script:

```
notion_engine/run_notion_updates.py
```

Responsibilities:

* Pull rows from the Notion database
* Run LLM classification
* Update Notion fields
* Exit

This job **does not generate reports or send emails**.

---

## Job 2 — Daily Briefing Engine

Entry script:

```
daily_briefing/run_daily_briefing.py
```

Responsibilities:

* Gather information from multiple sources
* Build the daily briefing
* Send the email

This job **does not mutate the Notion database**.

---

# Source Abstraction

The daily briefing engine should treat every input as a "source".

Example interface:

```
class BriefingSource:

    def fetch(self):
        return {}
```

Each source returns structured data.

---

## Notion Source

File:

```
daily_briefing/sources/notion_source.py
```

Responsibilities:

* Read data from Notion
* Provide information needed for the briefing

Example output:

```
{
    "unread_items": [...],
    "followups": [...],
    "stats": {...}
}
```

---

## Weather Source (Future)

File:

```
daily_briefing/sources/weather_source.py
```

Example output:

```
{
    "weather_summary": "Sunny, 72°F"
}
```

---

## Calendar Source (Future)

File:

```
daily_briefing/sources/calendar_source.py
```

Example output:

```
{
    "meetings_today": [...]
}
```

---

# Briefing Composition

File:

```
daily_briefing/compose_briefing.py
```

Responsibilities:

* Collect data from all sources
* Combine data
* Generate the daily report

Example:

```
def build_briefing():

    notion_data = NotionSource().fetch()

    weather_data = WeatherSource().fetch()

    combined = {
        **notion_data,
        **weather_data
    }

    return generate_report(combined)
```

---

# Scheduling

The two jobs should run independently.

Example schedule:

```
6:20 AM — run_notion_updates.py
6:30 AM — run_daily_briefing.py
```

This ensures the briefing reads the latest updated Notion data.

---

# Migration Strategy

Step 1

Create new folders:

```
notion_engine/
daily_briefing/
```

Step 2

Move files:

```
notion_service.py
llm_analysis.py
update_notion.py
```

→ notion_engine/

Step 3

Move reporting logic:

```
daily_report.py
report_delivery.py
```

→ daily_briefing/

Step 4

Create new entrypoints:

```
run_notion_updates.py
run_daily_briefing.py
```

Step 5

Add source abstraction under:

```
daily_briefing/sources/
```

---

# Long-Term Vision

The Daily Briefing Engine can eventually combine:

* Notion tasks
* Weather
* Calendar
* News
* Personal metrics

All sources feed a single daily briefing system.

This architecture allows the project to grow into a flexible personal operations assistant without complicating the Notion automation layer.
