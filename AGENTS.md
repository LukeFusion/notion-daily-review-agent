# AGENTS.md

This file defines how AI agents should understand and extend the current repository.

## System Overview

The project is split into two cooperating subsystems:

- `notion_engine/` handles Notion read, LLM classification, and Notion write-back.
- `daily_briefing/` gathers source data, builds the markdown briefing, saves it, and emails it.

Typical execution order:

1. `notion_engine/run_notion_updates.py`
2. `daily_briefing/run_daily_briefing.py`

`review_agent.py` remains as the compatibility entrypoint for the full flow.

## notion_engine Responsibilities

`notion_engine/` is responsible for operational work against the Notion database:

- reading pages from the configured Notion data source
- normalizing page properties into Python dictionaries
- sending unread items to the OpenAI-backed classifier
- preparing update payloads
- writing `Status`, `Type`, `AI Summary`, `AI Category`, and `AI Action` back to Notion

Key files:

- `notion_engine/notion_service.py`
- `notion_engine/llm_analysis.py`
- `notion_engine/update_notion.py`
- `notion_engine/run_notion_updates.py`

## daily_briefing Responsibilities

`daily_briefing/` is responsible for briefing generation and delivery:

- loading data from registered sources
- combining source output into one briefing data structure
- generating the markdown report body and subject line
- saving reports under `reports/`
- sending the report by SMTP when email settings are configured

Key files:

- `daily_briefing/compose_briefing.py`
- `daily_briefing/daily_report.py`
- `daily_briefing/report_delivery.py`
- `daily_briefing/run_daily_briefing.py`

## Sources Architecture

Sources live in `daily_briefing/sources/` and each implements a `fetch()` method that returns a dictionary of structured data.

Current sources:

- `notion_source.py` returns `all_items` and `unread_items`
- `calendar_source.py` returns `calendar_events`

Sources are registered in `daily_briefing/sources/registry.py`. The composer iterates through the registered sources and merges each source's returned dictionary into a combined data object.

Future sources should follow the same pattern, for example weather, news, stocks, or personal metrics.

## How compose_briefing Works

`daily_briefing/compose_briefing.py` is the bridge between raw sources and report generation.

It currently:

1. loads all registered sources from `registry.py`
2. calls `fetch()` on each source
3. merges the returned dictionaries into one `combined_data` object
4. reads `all_items` and `unread_items` from the Notion source output
5. runs LLM analysis on unread items so the briefing can use the same classification shape as the Notion engine
6. returns a compact structure consumed by `daily_report.generate_daily_briefing()`

## How LLM Is Used

LLM usage is centralized in `notion_engine/llm_analysis.py`.

The model is used to classify unread Notion items into:

- `summary`
- `tag`
- `action`

That output is reused in two places:

- `notion_engine/run_notion_updates.py` to prepare Notion write-back
- `daily_briefing/compose_briefing.py` so the report can prioritize and summarize unread items

`daily_briefing/daily_report.py` itself is deterministic formatting and reporting logic. It does not call the LLM directly.

## Adding a New Source

To add a new source:

1. create a new file under `daily_briefing/sources/`
2. implement a class with a `fetch() -> dict` method
3. return a namespaced dictionary payload that will merge safely with other sources
4. register the source in `daily_briefing/sources/registry.py`
5. update `daily_briefing/compose_briefing.py` only if the new source needs explicit extraction into the final briefing payload
6. update `daily_briefing/daily_report.py` if the new data should appear in the rendered report

Prefer extending the source system over adding special-case logic directly to the entrypoints.

## Configuration Notes

Runtime configuration comes from `.env`.

Important variables include:

- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `OPENAI_API_KEY`
- `GOOGLE_SERVICE_ACCOUNT_FILE`
- `GOOGLE_CALENDAR_ID`
- SMTP settings for email delivery

Secrets and key files must remain untracked.

---

# Example: Adding Weather

1. Create:

```
daily_briefing/sources/weather_source.py
```

2. Implement:

```python
class WeatherSource:
    def fetch(self):
        return {
            "weather": {...}
        }
```

3. Register in `registry.py`

4. Update `daily_report.py`

---

# System Goal

The system should scale from:

```
1 source → many sources
```

without requiring architectural changes.

---

# Summary

This repo is a:

**Modular, multi-source, AI-powered daily briefing system**

Agents should:

- extend via sources
- preserve architecture
- avoid tight coupling
- keep system composable
