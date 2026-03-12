# Daily Briefing Architecture

This document describes the long-term design of the Daily Briefing system.

The goal is to aggregate multiple information sources into a single morning report email.

---

# System Goal

The Daily Briefing Engine collects data from **N independent sources** and composes a single narrative report.

Example inputs:

- Notion tasks and reminders
- Calendar events
- Weather
- News
- Stocks
- Personal metrics
- Email summaries

All sources feed a single morning briefing.

---

# System Architecture

Sources → Composer → Report Generator → Email Delivery

Example source modules:

daily_briefing/sources/
    notion_source.py
    weather_source.py
    calendar_source.py
    news_source.py

Each source implements a `fetch()` function that returns structured data.

Example:

```python
class WeatherSource:

    def fetch(self):
        return {
            "weather": {
                "summary": "Sunny",
                "high": 72,
                "low": 55
            }
        }
```

---

# Source Pattern

Every source should follow the same structure:

```python
class Source:

    def fetch(self) -> dict:
        ...
```

The `fetch()` method returns a dictionary of structured data.

---

# Data Flow

Morning execution pipeline:

1. Notion Engine updates the database

notion_engine/run_notion_updates.py

2. Daily Briefing Engine runs

daily_briefing/run_daily_briefing.py

3. Composer collects data from all sources

daily_briefing/compose_briefing.py

4. Data is passed to the report generator

daily_briefing/daily_report.py

5. Email report is sent

daily_briefing/report_delivery.py

---

# Example Execution Flow

NotionSource  
WeatherSource  
CalendarSource  

↓  

compose_briefing()

↓

generate_daily_briefing()

↓

send_report_email()

---

# Design Principles

1. Sources are independent modules
2. The composer merges source data
3. The report generator creates narrative output
4. New sources can be added without modifying the entrypoint

---

# Adding a New Source

Create a new file in:

daily_briefing/sources/

Example:

weather_source.py

Steps:

1. Implement `fetch()`
2. Register the source in the source registry

No other system changes should be required.

---

# Example Future Sources

weather_source.py  
calendar_source.py  
news_source.py  
stocks_source.py  
health_source.py  

---

# Target System

N data sources  
      ↓  
compose_briefing()  
      ↓  
generate_daily_briefing()  
      ↓  
morning email report  

The system should scale from **1 source → many sources** without architectural changes.
