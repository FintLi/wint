---
name: vps-incident-diagnostics
description: Linux VPS host diagnosis for the user's RackNerd server. Use when SSH or root login fails, the server is unreachable, DNS/routing/firewall/open-port behavior looks wrong, CPU/RAM/swap/disk/inodes are exhausted, generic `systemd` services or cron/timers are failing, or you are not yet sure whether a failure is host-level or app-level. Use this before OpenClaw-specific debugging.
---

# VPS Incident Diagnostics

Use this skill when the task is mainly about **the VPS itself** rather than any one application. This skill is for host-level diagnosis first: system health, connectivity, services, storage, scheduling, and process state.

## Priority Order

Always narrow VPS problems in this order:

1. **Can we reach and log into the host?**
2. **Is the host healthy?** CPU, memory, disk, time, kernel, failed units
3. **Is networking sane?** routes, listeners, DNS, firewall, SSH
4. **Are scheduled jobs and long-running services healthy?**
5. **Only then debug a specific app** such as OpenClaw or `CLIProxyAPI`

## Quick Start

1. Read `references/host-baseline.md` for the current known-good map of this VPS.
2. Read `references/live-access.md` for the `.env` key mapping, then source the project root `.env` if you need live login values.
3. Run `scripts/collect_vps_health_snapshot.expect` to rebuild the live host snapshot.
4. Use `references/vps-runbook.md` to match symptoms to checks.
5. If the VPS is healthy and the issue becomes app-specific, hand off to the relevant app skill.

## What This Skill Covers

- SSH reachability and login configuration
- host identity, uptime, load, CPU, RAM, swap
- disk, inode, mount, and filesystem pressure
- network interfaces, routes, DNS, open ports, firewall state
- failed or flapping `systemd` services
- cron and timer failures
- suspicious high-resource processes
- current app footprint on this host, including OpenClaw, the First Stand notifier, `wireproxy`, and `CLIProxyAPI`

## Standard Workflow

### 1. Rebuild the host snapshot

Load the project root `.env`, then run `scripts/collect_vps_health_snapshot.expect`:

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a
```

The snapshot helper reads `VPS_HOST`, `VPS_PORT`, `VPS_USER`, and `VPS_PASSWORD` from that environment.

This gives you one compact host-level snapshot of:

- OS, kernel, time, uptime
- CPU, memory, swap, disk, inodes
- network interfaces, routes, listeners, resolver state
- SSH and failed unit status
- timers and cron clues
- top CPU / memory processes
- app-specific services currently relevant on this VPS

### 2. Decide which host layer is bad

Use these buckets:

- **Access layer**: cannot SSH, wrong port, root login policy, password auth policy
- **Resource layer**: RAM exhausted, swap thrash, CPU pegged, disk full, inode exhaustion
- **Network layer**: route missing, DNS broken, firewall blocking, port not listening
- **Supervisor layer**: `systemd`, cron, timers, services flapping or not enabled
- **Application layer**: host is fine, but one app is broken

### 3. Only escalate to app debugging after host checks pass

If the host has resource or network problems, fix those before trying to debug OpenClaw or notifier logic.

## Working Rules

- Live access values now live in the project root `.env`; `references/live-access.md` only documents the key names and loading pattern.
- Even though credentials are available locally through the project root `.env`, do not casually repeat them in ordinary handoff messages unless needed.
- Prefer a fresh snapshot over assumptions.
- Start broad, then narrow: host → service → app.
- Keep remediation scoped. Do not update packages or reboot unless the evidence clearly points there.

## What To Read

- `references/host-baseline.md`: current host inventory and known installed components
- `references/vps-runbook.md`: symptom-driven VPS diagnosis playbook
- `references/live-access.md`: `.env` key mapping for host access material
- `scripts/collect_vps_health_snapshot.expect`: one-command VPS snapshot helper
