# Project Agents

## Core Rules

- Source live VPS, Feishu, gateway, and auth values from `/Users/fint/Public/projects/wint/.env`.
- Do not reintroduce raw secrets into repository docs, skills, or code comments.
- Patch local project files first; deploy to the VPS only after a narrow local validation succeeds.

## Project Skills

- `skills/vps-incident-diagnostics/SKILL.md`: use for SSH, network, DNS, disk, memory, systemd, cron, or any unsure host-level incident.
- `skills/openclaw-vps-ops/SKILL.md`: use for live OpenClaw gateway, auth, runtime, notifier-incident, or CLIProxyAPI diagnosis after host checks pass.
- `skills/openclaw-feature-builder/SKILL.md`: use when adding or changing features in `/Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py`, including new sections, reminders, cards, data sources, CLI flags, scheduling behavior, or dedupe/state logic.
