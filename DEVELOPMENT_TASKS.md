# Development Tasks

This file tracks the step-by-step implementation of the architecture refactor described in:

ARCHITECTURE_REFACTOR_PLAN.md

The refactor separates two systems:

1. Notion Engine (data processing + Notion updates)
2. Daily Briefing Engine (email briefing + external data sources)

Codex should execute tasks **in order** and stop after completing each step so the changes can be reviewed.

---

# Task 1 — Create New Directory Structure

Create the following folders:

notion_engine/
daily_briefing/
daily_briefing/sources/

Do not move files yet.

Expected result:

project-root/

notion_engine/
daily_briefing/
daily_briefing/sources/

---

# Task 2 — Move Notion Processing Files

Move these files into:

notion_engine/

Files:

notion_service.py
llm_analysis.py
update_notion.py

Update imports so they still resolve.

Do not change logic.

---

# Task 3 — Move Reporting Files

Move these files into:

daily_briefing/

Files:

daily_report.py
report_delivery.py

Update imports as necessary.

Do not change functionality.

---

# Task 4 — Create Notion Engine Entrypoint

Create:

notion_engine/run_notion_updates.py

Responsibilities:

• run the existing Notion classification pipeline
• update Notion fields
• exit

This script should contain only the logic required to:

1. read Notion rows
2. run LLM analysis
3. write updates back to Notion

No reporting or email functionality.

---

# Task 5 — Create Daily Briefing Entrypoint

Create:

daily_briefing/run_daily_briefing.py

Responsibilities:

• gather data sources
• generate daily report
• send email

This script should:

1. fetch Notion data
2. generate the briefing
3. send the email

---

# Task 6 — Introduce Source Abstraction

Create a source system under:

daily_briefing/sources/

Create file:

notion_source.py

This should read data from Notion and return structured data used by the briefing.

Example output:

{
  "items": [],
  "stats": {},
  "followups": []
}

---

# Task 7 — Create Briefing Composer

Create file:

daily_briefing/compose_briefing.py

Responsibilities:

• collect data from all sources
• combine into one structure
• pass to daily_report generator

Example:

notion_data = NotionSource().fetch()

combined_data = {
    **notion_data
}

generate_report(combined_data)

---

# Task 8 — Verify Execution

Confirm both jobs run independently:

Notion engine:

python notion_engine/run_notion_updates.py

Daily briefing:

python daily_briefing/run_daily_briefing.py

Both scripts should execute without errors.

---

# Rules for Codex

1. Follow tasks sequentially.
2. Do not modify application logic unless necessary.
3. Prioritize safe refactoring.
4. After completing each task, explain what changed.