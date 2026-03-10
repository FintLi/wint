---
name: openclaw-vps-ops
description: OpenClaw application diagnosis and repair on the user's RackNerd Debian VPS. Use only after host-level checks pass, for `openclaw` binary or gateway issues, `openclaw agent` runtime failures, auth/config drift under `/root/.openclaw`, First Stand→Feishu notifier bugs, Feishu card delivery/content issues, or `CLIProxyAPI` app wiring. Do not use for SSH, network, disk, memory, or generic VPS incidents.
---

# OpenClaw VPS Ops

Use this skill when the problem is mainly **OpenClaw or its app-level integrations on the live VPS**.

If the symptom might actually be a host problem — SSH/login, DNS/routing, firewall, disk full, RAM pressure, CPU saturation, failed user bus, broken cron/systemd, or general VPS instability — switch to `$vps-incident-diagnostics` first. This skill assumes the VPS is reachable and basically healthy.

## Scope Boundary

This skill owns:

- `/usr/bin/openclaw`, `openclaw agent`, and gateway behavior
- auth/config drift under `/root/.openclaw`
- the root user gateway unit at `/root/.config/systemd/user/openclaw-gateway.service`
- the First Stand → Feishu notifier code, wrappers, env, logs, and state
- the separately installed `CLIProxyAPI` binary and any app-level wiring around it
- the local OpenAI auth input referenced through `OPENAI_AUTH_JSON_PATH` in the project root `.env`

This skill does not own:

- SSH access and root password handling
- host reachability, DNS, routing, firewall, or open-port confusion
- CPU / RAM / swap / disk / inode pressure
- generic `systemd`, timer, or cron failures that affect the whole host

## Quick Start

1. Read `references/deployment-map.md` for the current app topology and boundaries.
2. Read `references/live-secrets.md` for the `.env` key mapping, then source the project root `.env` if you need live values.
3. If live state may have changed, run `scripts/collect_vps_snapshot.expect`.
4. For OpenClaw core incidents, read `references/openclaw-diagnostics.md`.
5. Only after OpenClaw core is healthy should you use `references/troubleshooting.md` for notifier or `CLIProxyAPI` issues.

## Priority Order

Always debug in this order:

1. **Confirm the host is basically healthy**; otherwise hand off to `$vps-incident-diagnostics`
2. **OpenClaw binary and gateway health**
3. **OpenClaw auth and config state**
4. **A minimal `openclaw agent` probe**
5. **Notifier wrappers, env, logs, state, and Feishu delivery**
6. **`CLIProxyAPI` installation or wiring**

## Standard Workflow

### 1. Rebuild the live app snapshot

Load the project root `.env`, then run `scripts/collect_vps_snapshot.expect`:

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a
```

The snapshot helper reads `VPS_HOST`, `VPS_PORT`, `VPS_USER`, and `VPS_PASSWORD` from that environment.

This one-pass snapshot is the default first step because it shows:

- OpenClaw binary and version
- gateway service status and unit file shape
- remote OpenClaw files under `/root/.openclaw`
- notifier env, wrappers, cron, logs, and state
- `CLIProxyAPI` install status

### 2. Classify the failure

Treat it as **OpenClaw core** when any of these are true:

- `openclaw agent` itself errors or returns no text payload
- gateway service is inactive, flapping, or listening on the wrong port
- auth files under `/root/.openclaw` are missing or look stale
- current runtime and available version drift look suspicious
- downstream scripts fail during the model call

Treat it as **downstream** only when:

- gateway is healthy
- a minimal `openclaw agent` probe succeeds
- only wrappers, cron, Feishu cards, news content, or dedupe state are broken

### 3. Prefer remote runtime truth

- Local notifier source of truth is `tools/firststand_feishu_digest.py`.
- Live deployed notifier code is `/opt/openclaw-firststand/firststand_feishu_digest.py`.
- OpenClaw runtime truth lives on the VPS under `/root/.openclaw` and the gateway unit.

When debugging runtime, prefer remote state over assumptions from local code.

### 4. Validate narrow to broad

Use the smallest proof that isolates the failing layer:

1. `openclaw --version`
2. `systemctl --user status openclaw-gateway`
3. gateway logs and port `18789`
4. existence and timestamps of `/root/.openclaw/*`
5. a minimal `openclaw agent --agent main --message 'ping' --thinking low --json`
6. only then the notifier wrapper or a real Feishu send

## Working Rules

- Live app secrets now live in the project root `.env`; `references/live-secrets.md` only documents the key names and loading pattern.
- VPS login material lives in `$vps-incident-diagnostics`, not here.
- Even though secrets are available locally through the project root `.env`, avoid re-pasting them into ordinary answers unless needed for the task.
- Patch local code first, then deploy remotely.
- For OpenClaw incidents, inspect runtime files and service state before editing notifier logic.
- For notifier incidents, inspect the newest artifacts under `/var/lib/openclaw-firststand/` before guessing.
- Treat `CLIProxyAPI` as a separate app concern unless the user explicitly wants it wired into OpenClaw or the notifier.

## What To Read

- `references/deployment-map.md`: current live map of the app stack
- `references/live-secrets.md`: `.env` key mapping for app-level secrets and auth inputs
- `references/openclaw-diagnostics.md`: OpenClaw-first runbook
- `references/troubleshooting.md`: notifier and adjacent symptom guide
- `scripts/collect_vps_snapshot.expect`: one-command redacted app snapshot
