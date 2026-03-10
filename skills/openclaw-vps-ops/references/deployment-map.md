# OpenClaw VPS Deployment Map

Snapshot date: 2026-03-09 (Asia/Shanghai)

This file maps the OpenClaw-related application stack on the user's RackNerd VPS. It is intentionally app-scoped. For SSH access, host health, network, storage, or generic service failures, use `/Users/fint/Public/projects/wint/skills/vps-incident-diagnostics/` first.

## 1. Deployment Target

- Provider / label: RackNerd `2.5 GB KVM VPS (Black Friday 2025)`
- Hostname: `racknerd-3449ef7`
- Public IP: `107.175.194.23`
- OS seen during snapshot: Debian 12 (`bookworm`)

Host identity is included only for orientation. Treat the VPS skill as the source of truth for host-level diagnosis.

## 2. OpenClaw Core

### Live runtime

- Binary path: `/usr/bin/openclaw`
- Observed version on 2026-03-09: `2026.3.2`
- Observed `openclaw agent --help` works on the VPS
- Runtime workspace/config root: `/root/.openclaw`

### Gateway service

- Unit path: `/root/.config/systemd/user/openclaw-gateway.service`
- Unit name: `openclaw-gateway.service`
- Observed status on 2026-03-09: `active (running)`
- Gateway port in the unit file: `18789`
- The unit file contains sensitive environment values; do not dump it verbatim into chat.
- Snapshot note: gateway logs reported that `v2026.3.7` was available while runtime was `v2026.3.2`; verify live before updating.

### Config and auth files

- Main config directory: `/root/.openclaw`
- Important remote file: `/root/.openclaw/openclaw.json`
- Backup file: `/root/.openclaw/openclaw.json.bak`
- Remote workspace subtree: `/root/.openclaw/workspace`
- These files are sensitive. Confirm existence, size, and timestamps before asking to inspect contents.

## 3. Secret Split

At the user's explicit request, the repo stores live secret material, but it is now split by responsibility:

- Actual live values now live in the project root `.env`, which is gitignored.
- `/Users/fint/Public/projects/wint/skills/vps-incident-diagnostics/references/live-access.md` documents the VPS access key names.
- `references/live-secrets.md` documents the app-level key names, including `OPENAI_AUTH_JSON_PATH`.

## 4. First Stand → Feishu Pipeline

### Local source of truth

- Main source file: `/Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py`
- Backup file: `/Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py.bak`
- Supporting research doc: `/Users/fint/Public/projects/wint/docs/openclaw-玩法与变现研究-2026-03-07.md`

### Remote deployed files

- Deployed script: `/opt/openclaw-firststand/firststand_feishu_digest.py`
- Env file: `/etc/openclaw-firststand.env`
- Daily wrapper: `/usr/local/bin/openclaw-firststand-feishu`
- Prematch wrapper: `/usr/local/bin/openclaw-firststand-prematch`
- Cron file: `/etc/cron.d/openclaw-firststand-feishu`

### Env keys currently expected

- `FEISHU_WEBHOOK`
- `OPENCLAW_AGENT`
- `LPL_FOCUS_TEAMS`
- `PREMATCH_ALERT_WINDOW_HOURS`

### Current scheduler behavior

- Daily digest: `35 9 8-22 3 *`
- Prematch check: `5 * 15-22 3 *`
- Time zone: `Asia/Shanghai`

### Remote state and logs

- State directory: `/var/lib/openclaw-firststand`
- Digest log: `/var/log/openclaw-firststand.log`
- Prematch log: `/var/log/openclaw-firststand-prematch.log`

### Important state files

- `/var/lib/openclaw-firststand/last_digest.txt`
- `/var/lib/openclaw-firststand/last_digest_context.json`
- `/var/lib/openclaw-firststand/last_prematch.txt`
- `/var/lib/openclaw-firststand/last_prematch_context.json`
- `/var/lib/openclaw-firststand/prematch_sent.json`

### Current notifier design facts

- Daily report sends multiple separate Feishu interactive cards, not one giant message.
- Prematch reminder sends a dedicated interactive card for LPL-related matches.
- LPL focus teams are currently `BLG,JDG`.
- Prematch alert window is currently `12` hours.
- The script can infer group-stage matchups when official `lolesports` events still show `TBD`.
- Fallback-inferred pairings must still be labeled as pending official confirmation.
- Inline card images are limited by the current Feishu custom-bot webhook mode because no `img_key` upload flow is configured.

## 5. CLIProxyAPI Sidecar

- Observed binary path: `/usr/local/bin/CLIProxyAPI`
- Observed version on 2026-03-09: `6.8.47`
- No live config or service wiring is treated as canonical in this repo yet.
- Treat it as an adjacent app install until the user asks for deeper integration.

## 6. Best Validation Surfaces

When debugging app behavior, inspect these first:

- `/root/.config/systemd/user/openclaw-gateway.service`
- `/root/.openclaw/openclaw.json`
- `/etc/openclaw-firststand.env`
- `/var/lib/openclaw-firststand/last_digest_context.json`
- `/var/lib/openclaw-firststand/last_prematch_context.json`
- `/var/lib/openclaw-firststand/prematch_sent.json`

Prefer redacted inspection or metadata over pasting raw secret-bearing contents.

## 7. Safe Change Loop

Use this order for code changes:

1. Patch local source in `/Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py`.
2. Copy the exact file to `/opt/openclaw-firststand/firststand_feishu_digest.py`.
3. Run `python3 -m py_compile` on the deployed copy.
4. Run the narrowest wrapper or direct script command that proves the fix.
5. Re-check state files and logs.

If the failure occurs before the notifier runs, go back to OpenClaw core checks before changing downstream code.
