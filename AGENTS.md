# Notion Daily Review Agent

This project contains the first working version of a daily Notion review pipeline.

## Current scope (v1)
- Load credentials and IDs from `.env`
- Connect to Notion
- Pull rows where `Status = Unread`
- Normalize them into structured Python objects
- Print results to terminal

## Planned next steps
- LLM analysis of unread items
- Daily markdown report generation
- Notion updates (`Status` and inferred `Type`)
