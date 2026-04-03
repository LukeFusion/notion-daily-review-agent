# Notion Daily Review Agent

This repository is an archived, deprecated version of an older daily review automation.

The automation has been intentionally disabled. Running the documented entrypoints now exits immediately without loading credentials or making Notion, OpenAI, Google Calendar, or SMTP calls.

See [SYSTEM_OVERVIEW.md](/Users/lukesquire/projects/notion-daily-review-agent/SYSTEM_OVERVIEW.md) and [DAILY_BRIEFING_ARCHITECTURE.md](/Users/lukesquire/projects/notion-daily-review-agent/DAILY_BRIEFING_ARCHITECTURE.md) for historical architecture notes.

## Archived Scope
This project originally:

1. Read Notion capture rows.
2. Analyzed unread items with OpenAI.
3. Updated Notion properties.
4. Generated a daily markdown briefing.
5. Optionally sent the briefing by email.

## Current Status
- `review_agent.py` is a no-op deprecation entrypoint.
- `notion_engine/run_notion_updates.py` is a no-op deprecation entrypoint.
- `daily_briefing/run_daily_briefing.py` is a no-op deprecation entrypoint.
- Existing implementation files are retained for reference only.

## Before Pushing To GitHub
1. Confirm local secrets are not tracked:
   ```bash
   git ls-files .env
   git ls-files 'Keys/*'
   ```
2. Confirm common secret patterns are absent from tracked files:
   ```bash
   rg -n "sk-|ntn_|AIza|smtp|password|secret|private_key" --glob '!.env' --glob '!Keys/**' .
   ```
3. If you previously installed the macOS `launchd` job, unload and remove it locally so the old scheduler stops invoking this repo:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.notion.dailyreview.plist 2>/dev/null || true
   rm -f ~/Library/LaunchAgents/com.notion.dailyreview.plist
   ```
4. Rotate any credential that may have ever been stored in this repo or nearby local files before publishing.

## Repo Hygiene
- `.env` and `.env.*` are ignored.
- `Keys/` and `keys/` are ignored.
- Generated outputs such as `logs/`, `reports/`, and `state/` are ignored.
- `.env.example` contains blank placeholders only.
