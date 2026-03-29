See `SYSTEM_OVERVIEW.md` for the subsystem split and `DAILY_BRIEFING_ARCHITECTURE.md` for the multi-source briefing architecture.

# Notion Daily Review Agent

Automated Python agent that reviews your Notion capture database each morning, analyzes unread rows with OpenAI, updates Notion fields, and sends a hybrid operational email briefing.

## Why This Exists

This project is a personal daily briefing system that turns scattered inputs—tasks, reminders, calendar events, and (eventually) other signals like weather or news—into a single, structured morning report. Instead of checking multiple tools and mentally prioritizing your day, the system aggregates and analyzes everything for you, then delivers a concise narrative via email. The goal is to reduce cognitive overhead, surface what matters most, and create a repeatable “start of day” workflow that scales as new data sources are added.

## What It Does
1. Reads all Notion rows for context.
2. Identifies unread rows (`Status = Unread`) for actioning.
3. Sends unread rows to OpenAI for classification (`summary`, `tag`, `action`).
4. Updates unread rows in Notion:
   - `Status -> Reviewed`
   - `Type -> existing type or inferred tag`
   - `AI Summary`, `AI Category`, `AI Action`
5. Builds a hybrid morning briefing with:
   - short narrative orientation
   - top actions, follow-ups, inbox status
   - observations + weekly trends
   - worth revisiting + suggested plan
6. Saves markdown report in `reports/`.
7. Sends report by SMTP email if configured.

## Sample Output

**Subject:** Daily Briefing — March 13, 2026

### Daily Review Narrative

Today is Friday, March 13, 2026. Your schedule is front-loaded with two structured commitments, giving you a defined window to focus on key follow-ups before the afternoon. Your backlog remains manageable, with a small number of high-value actions that can be closed quickly to maintain momentum.

### Today's Schedule

- Certify for EDD Benefits — 10:45 AM  
- Monthly Goals Retro — 11:15 AM  

### Top Priorities

1. Send job outreach message to Tom Neyhart  
2. Follow up with Carolina on next steps  
3. Confirm documents for healthcare / domestic partnership  

### What's Still There

- Calendar digest setup (pending from earlier this week)  
- Basketball refereeing opportunities (exploration item)  

### Can Hold Off

- Recipe ideas and saved articles  
- General reading backlog  

### Suggested Plan

- Use early morning (before 10:45 AM) to complete outreach and admin tasks  
- Attend scheduled meetings with clear outcomes in mind  
- Block 30–60 minutes later today or this weekend for backlog review  

---

*This example is sanitized and does not contain real personal data.*

## Morning Briefing Format
- `## Daily Review Narrative`
- `## Top Actions Today`
- `## Follow-ups`
- `## Inbox Status`
- `## Observations`
- `## Weekly Trends`
- `## Worth Revisiting`
- `## Suggested Plan`

Subject line format:
- `Daily Briefing — {date} | {num_actions} actions | {num_followups} follow-ups | inbox {status}`

## Notion Schema Expectations
Required core properties:
- `Title` (title)
- `Status` (select)
- `Type` (select)
- `Source` (select)
- `Captured Date` (date)
- `Link` (url)
- `Raw Content` (rich_text)

Write-back properties (alias matching supported):
- `AI Summary` (rich_text)
- `AI Category` (select)
- `AI Action` (select)

## Project Structure
- `review_agent.py` - compatibility entrypoint for the full review pipeline
- `notion_engine/notion_service.py` - Notion reads + schema-aware property lookup
- `notion_engine/llm_analysis.py` - OpenAI classification for unread rows
- `notion_engine/update_notion.py` - Notion write-back
- `notion_engine/run_notion_updates.py` - analysis + Notion update workflow
- `daily_briefing/daily_report.py` - hybrid briefing generation + metrics history
- `daily_briefing/report_delivery.py` - SMTP sender
- `daily_briefing/compose_briefing.py` - briefing data assembly
- `daily_briefing/run_daily_briefing.py` - report-only entrypoint
- `config.py` - environment loading/validation

## Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set required `.env` values:
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- `OPENAI_API_KEY`

Optional email values:
- `REPORT_EMAIL_TO`
- `REPORT_EMAIL_FROM`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS`
- `GOOGLE_SERVICE_ACCOUNT_FILE`

## Google Calendar Source
To include today's Google Calendar events in the briefing:

1. Create a Google Cloud project and enable the Google Calendar API.
2. Create a service account and download its JSON key.
3. Store that JSON key outside the repo at a stable absolute path.
4. Set `GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json` in `.env`.
5. Share the calendar you want the briefing to read with the service account email and grant at least `See all event details` access.

When configured, the daily briefing adds a `## Today's Schedule` section with today's events.

## Run Manually
```bash
python3 review_agent.py
```

Alternative entrypoints:
```bash
python3 notion_engine/run_notion_updates.py
python3 daily_briefing/run_daily_briefing.py
```

## Schedule at 6:30am Pacific (macOS launchd)
Create `~/Library/LaunchAgents/com.notion.dailyreview.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.notion.dailyreview</string>
    <key>ProgramArguments</key>
    <array>
      <string>/ABS/PATH/TO/.venv/bin/python3</string>
      <string>/ABS/PATH/TO/review_agent.py</string>
    </array>
    <key>WorkingDirectory</key><string>/ABS/PATH/TO/PROJECT</string>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key><integer>6</integer>
      <key>Minute</key><integer>30</integer>
    </dict>
    <key>StandardOutPath</key><string>/ABS/PATH/TO/PROJECT/logs/daily_review.out.log</string>
    <key>StandardErrorPath</key><string>/ABS/PATH/TO/PROJECT/logs/daily_review.err.log</string>
    <key>RunAtLoad</key><false/>
  </dict>
</plist>
```

Load/reload:
```bash
mkdir -p logs
launchctl unload ~/Library/LaunchAgents/com.notion.dailyreview.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.notion.dailyreview.plist
launchctl list | rg notion.dailyreview
```

## Deploying to GitHub
1. Verify `.env` is not tracked:
   ```bash
   git ls-files .env
   ```
2. Verify no secrets in tracked files:
   ```bash
   rg -n "sk-proj|ntn_|SMTP_PASSWORD|NOTION_API_KEY" --glob '!.env' .
   ```
3. Commit project files:
   ```bash
   git add .
   git commit -m "Initial Notion daily review agent"
   ```
4. Push to GitHub:
   ```bash
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

## CI
GitHub Actions workflow included:
- `.github/workflows/ci.yml`
- Runs dependency install and Python syntax checks on push/PR.

## Security Notes
- `.env` is gitignored.
- Keep `.env.example` placeholders only.
- If any credential was ever exposed, rotate it before deployment.
