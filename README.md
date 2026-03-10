# wint

A small collection of handy tools.

## Structure

- `tools/`: core utility scripts and helpers.
- `playground/`: a scratch space for experiments, drafts, and temporary demos.

## Chrome bookmarks tools

### `chrome_bookmarks_organizer.py`

`/Users/fint/Public/projects/wint/tools/chrome_bookmarks_organizer.py` can scan Chrome bookmarks, check link health, and generate a JSON report.

Common examples:

```bash
python3 tools/chrome_bookmarks_organizer.py --list-profiles
python3 tools/chrome_bookmarks_organizer.py --profile Fint
python3 tools/chrome_bookmarks_organizer.py --profile Fint --max-checks 50
```

### `chrome_bookmarks_rebuilder.py`

`/Users/fint/Public/projects/wint/tools/chrome_bookmarks_rebuilder.py` rebuilds bookmarks from an original backup file and writes the result back to a target Chrome profile.

What it does:

- Uses the backup bookmark file as the source of truth.
- Keeps the original folder tree but clears old bookmark items.
- Rebuilds new categorized folders directly at the top level.
- Creates multi-level Chinese folders.
- References the meaning of the original folder taxonomy when deciding where to place bookmarks.
- Skips confirmed dead links, but keeps `unreachable` and `skipped` links.
- Creates a timestamped backup before writing.

Example:

```bash
python3 tools/chrome_bookmarks_rebuilder.py \
  --source-bookmarks-file playground/chrome_bookmarks_backups/Bookmarks.20260306-174246.bak \
  --profile Fint \
  --target-root other \
  --report-file playground/chrome_bookmarks_rebuild_applied.json \
  --apply
```

## VPS diagnostics skill

This repo also includes a dedicated VPS troubleshooting skill for host-level incidents.

Key files:

- `skills/vps-incident-diagnostics/SKILL.md`: VPS-first diagnosis workflow.
- `skills/vps-incident-diagnostics/references/host-baseline.md`: current host inventory and installed components.
- `skills/vps-incident-diagnostics/references/vps-runbook.md`: symptom-driven runbook for SSH, network, resource, disk, and systemd issues.
- `skills/vps-incident-diagnostics/references/live-access.md`: `.env` key mapping for VPS login material.
- `skills/vps-incident-diagnostics/scripts/collect_vps_health_snapshot.expect`: one-command host snapshot helper.

## OpenClaw ops skill

This repo also includes an OpenClaw troubleshooting skill pack for app-level incidents on the live VPS.

Use it only after host-level checks pass. SSH, network, disk, memory, and generic service failures belong to the VPS skill above.

Key files:

- `skills/openclaw-vps-ops/SKILL.md`: trigger and workflow for OpenClaw-first diagnosis and repair.
- `skills/openclaw-vps-ops/references/deployment-map.md`: app topology, runtime paths, and the boundary with the VPS skill.
- `skills/openclaw-vps-ops/references/openclaw-diagnostics.md`: OpenClaw core runbook for gateway, auth, config, and version drift.
- `skills/openclaw-vps-ops/references/troubleshooting.md`: notifier, Feishu, and `CLIProxyAPI` symptom guide after core health is confirmed.
- `skills/openclaw-vps-ops/references/live-secrets.md`: `.env` key mapping for app-level secrets.
- Project root `.env`: gitignored live secret source for VPS, Feishu, gateway token, and local auth path.
- `skills/openclaw-vps-ops/scripts/collect_vps_snapshot.expect`: redacted OpenClaw/app snapshot helper.

## Cunzhen execution package

This repo now includes a practical execution package for the `村圳` Shenzhen urban-village rental MVP.

Key files:

- `docs/cunzhen/quick-cash-plan-2026-03-09.md`: 14/30/60 day quick-revenue operating plan.
- `docs/cunzhen/mvp-spec-2026-03-09.md`: MVP product scope and business rules.
- `docs/cunzhen/supply-ops-sop-2026-03-09.md`: supply acquisition and fulfillment SOP.
- `docs/cunzhen/content-playbook-2026-03-09.md`: content, DM, and conversion playbook.
- `docs/cunzhen/dashboard-metrics-2026-03-09.md`: KPI definitions and review cadence.
- `docs/cunzhen/week-1-launch-checklist-2026-03-09.md`: day-by-day launch checklist for the first 7 days.
- `docs/cunzhen/first-batch-content-scripts-2026-03-09.md`: ready-to-publish short-form content scripts.
- `docs/cunzhen/form-setup-guide-2026-03-09.md`: exact Feishu/WeChat form setup and field design.
- `docs/cunzhen/outreach-and-dm-scripts-2026-03-09.md`: renter and partner outreach copy.
- `templates/cunzhen/*.csv`: listing, lead, viewing, content, settlement, and form-export templates.
- `tools/cunzhen_unit_economics.py`: unit economics calculator for different growth scenarios.

Example:

```bash
python3 tools/cunzhen_unit_economics.py --scenario target-60d
python3 tools/cunzhen_unit_economics.py --scenario fast-cash
python3 tools/cunzhen_unit_economics.py --scenario lean --leads 80 --avg-fee 550
```

## AI news Feishu digest

`/Users/fint/Public/projects/wint/tools/ai_news_feishu_digest.py` builds a daily AI news digest for Feishu.

Highlights:

- fixed China-time window: yesterday `08:00` to today `08:00`
- picks up to 10 items, preferring official first-party sources
- falls back to a second tier of reliable media when official items are insufficient
- sends one Feishu interactive card per story with a direct source link
- records candidate new first-party domains under the runtime state directory for manual review

Examples:

```bash
python3 /Users/fint/Public/projects/wint/tools/ai_news_feishu_digest.py \
  --datetime 2026-03-09T08:30:00+08:00

python3 /Users/fint/Public/projects/wint/tools/ai_news_feishu_digest.py \
  --send \
  --datetime 2026-03-09T08:30:00+08:00
```

The source registry lives at `/Users/fint/Public/projects/wint/tools/ai_news_sources.json`.

## Cunzhen mini-program MVP

A native WeChat mini-program prototype now lives in `/Users/fint/Public/projects/wint/apps/cunzhen-miniapp`.

Highlights:

- renter flow: home, listings, listing detail, demand card, viewing booking
- invited supply flow: partner listing intake form
- operator view: funnel summary, risky listings, recent leads and viewings
- local business rules: required fields, 72-hour expiry, version snapshots, lead priority

Open `/Users/fint/Public/projects/wint/apps/cunzhen-miniapp/project.config.json` in WeChat DevTools to preview.

## Cunzhen API

A lightweight Node API now lives in `/Users/fint/Public/projects/wint/apps/cunzhen-api`.

Highlights:

- JSON-backed persistence with seed data bootstrap
- endpoints for listings, leads, viewings, supply intake, and admin summary
- ready to pair with the mini-program via `/Users/fint/Public/projects/wint/apps/cunzhen-miniapp/services/env.js`

Run it with:

```bash
cd /Users/fint/Public/projects/wint/apps/cunzhen-api
npm start
```
