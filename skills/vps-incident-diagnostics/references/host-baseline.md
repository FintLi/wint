# VPS Host Baseline

Snapshot date: 2026-03-09 (Asia/Shanghai)

This file describes the current known state of the RackNerd VPS. Treat it as a baseline, not a guarantee. Rebuild state with `scripts/collect_vps_health_snapshot.expect` before making risky decisions.

## Identity

- Provider / label: RackNerd `2.5 GB KVM VPS (Black Friday 2025)`
- Hostname: `racknerd-3449ef7`
- Public IP: `107.175.194.23`
- OS: Debian 12 (`bookworm`)
- Kernel seen in snapshot: `6.1.0-9-amd64`
- Default SSH port provided by user: `22`
- Primary login user: `root`

## Current notable services and installs

### OpenClaw

- CLI path: `/usr/bin/openclaw`
- Observed version: `2026.3.2`
- Gateway service type: `systemd --user` service for `root`
- Unit: `openclaw-gateway.service`
- Observed state in snapshot: `active (running)`
- Gateway port in service file: `18789`

### First Stand notifier

- Deployed under: `/opt/openclaw-firststand`
- Wrappers:
  - `/usr/local/bin/openclaw-firststand-feishu`
  - `/usr/local/bin/openclaw-firststand-prematch`
- Cron file: `/etc/cron.d/openclaw-firststand-feishu`
- State path: `/var/lib/openclaw-firststand`

### CLIProxyAPI

- Entry point: `/usr/local/bin/CLIProxyAPI`
- Observed version: `6.8.47`
- Release root: `/opt/cliproxyapi`
- Current conclusion: installed, but no active process or configured service was seen

### Other service clue from snapshot

- `wireproxy.service` appears enabled in unit-file listings

## Known host-level things worth checking during incidents

- `systemctl --failed`
- `systemctl list-unit-files | grep -i wireproxy`
- `systemctl --user status openclaw-gateway`
- `ss -ltnup`
- `df -hT` and `df -ih`
- `free -h` and `vmstat 1 5`
- `journalctl -p err -n 100 --no-pager`

## What “healthy enough” means here

Before diving into app bugs, confirm all of these:

- SSH works on `22`
- root can log in
- disk and inodes are not exhausted
- RAM and swap are not pinned
- there are no obvious failed units that explain the symptom
- DNS and routes look sane
- the expected service or port is actually listening
