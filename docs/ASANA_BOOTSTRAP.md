# Asana Bootstrap Record — Shadow-Garden Launcher

**Date:** 2026-07-08
**Branch:** `claude/nww-asana-connector-2gst3u`
**Account tier:** Free (portfolios + custom fields unavailable)

## Live GIDs (bootstrapped)

| Object | Name | GID |
|--------|------|-----|
| Workspace | (frederickpr10@gmail.com) | `1216280230062995` |
| Project | Shadow-Garden Voice Bridge | `1216393327456850` |
| Seed task | Baseline metrics — Shadow-Garden Voice Bridge | `1216393468002348` |

Project: https://app.asana.com/1/1216280230062995/project/1216393327456850

## Mode: free-tier fallback

The workspace is on Asana's **free tier**, where **portfolios** (Advanced only)
and **custom fields** (Starter+) are not available. The connector therefore runs
in `NWW_FREE_TIER_FALLBACK=true` mode:

- No portfolio is created; `ASANA_PORTFOLIO_ID` is left unset.
- Metrics are written into the **task description** plus a fenced
  **`Metrics JSON`** block (schema `nww.metrics.v1`) rather than custom fields.
- Planned fields — Resonance Score, Technique Mastery, Copy Technique Success,
  Soul Alignment, Last Reported, Metrics JSON — are carried as keys inside that
  JSON block.

## Additive to Jira — not a replacement

Asana reporting sits **alongside** the existing Jira-first flow. It does not
fork, alter, or break current Shadow Garden Jira behavior. It can be disabled
entirely via `DISABLE_ASANA=false` without affecting Jira.

## Upgrade path

On upgrade to a paid plan:
1. Create the 6 custom fields and attach them to project `1216393327456850`.
2. Record the field GIDs in `.env` (add `ASANA_CUSTOM_FIELD_*`).
3. Flip `ASANA_TIER=starter` (or higher) and `NWW_FREE_TIER_FALLBACK=false`.
4. The existing project + task GIDs remain valid — no re-bootstrap needed.
