---
name: openclaw-feature-builder
description: Build or modify features in the user's OpenClaw/“龙虾” First Stand→Feishu workflow. Use when adding a new daily digest section, prematch reminder, Feishu card layout, data source, dedupe or state rule, CLI flag, schedule-related app behavior, or other app-level capability in `tools/firststand_feishu_digest.py`, and when the task should be implemented, previewed, deployed to the RackNerd VPS, and verified end-to-end.
---

# OpenClaw Feature Builder

Use this skill when the task is about **adding or changing behavior** in the OpenClaw-driven First Stand → Feishu workflow.

If the task is mainly about:

- VPS reachability, SSH, DNS, disk, memory, or generic service health → use `$vps-incident-diagnostics`
- live OpenClaw gateway, auth, or runtime incidents → use `$openclaw-vps-ops`

## Quick Start

1. Read `references/feature-map.md` to classify the requested feature and find the right code touchpoints.
2. Read `references/validation-loop.md` before running previews, real sends, or remote deploys.
3. Load the project root `.env` before any command that touches the VPS or Feishu.
4. Patch local code first; do not start by editing live files on the VPS.
5. Validate from narrow to broad, and keep the newest artifacts under `/var/lib/openclaw-firststand` as proof.

## Common Triggers

Use this skill for requests like:

- “给龙虾新增一个功能”
- “给日报加一个新栏目”
- “给赛前提醒多发一条/多加一个模块”
- “给飞书卡片换布局或加按钮”
- “新增一个数据源或新的 dedupe 逻辑”
- “给脚本加一个命令行参数或新的调度行为”

## Workflow

### 1. Classify the feature first

Use these buckets:

- **Content feature**: new section, wording, links, card template, card order
- **Context feature**: new source data, new fields, new derived facts
- **Delivery feature**: new card type, new CLI flag, new schedule/app behavior
- **State feature**: dedupe, once-only send, remember-last-run behavior

If more than one bucket applies, work in this order:

1. context
2. prompt
3. parsing/rendering
4. CLI or state
5. deploy and verify

### 2. Patch the minimum surfaces that match the request

For a **new daily digest section**, expect to touch some or all of:

- `SECTION_TITLES`
- `SECTION_TEMPLATES`
- `build_context()`
- `build_digest_prompt()`
- `links_for_section()`
- `send_digest_cards()`

For a **new prematch section or reminder behavior**, expect to touch some or all of:

- `PREMATCH_SECTION_TITLES`
- `build_prematch_context()`
- `build_prematch_prompt()`
- `send_prematch_alert()`
- `maybe_send_prematch()`

For a **new CLI or schedule-facing behavior**, expect to touch some or all of:

- `main()` argument parsing
- env var reads in `main()`
- remote wrapper assumptions under `/usr/local/bin/openclaw-firststand-*`
- `/etc/cron.d/openclaw-firststand-feishu` if the schedule itself changes

### 3. Preserve the current architecture

Keep this sequence intact unless the request truly requires a redesign:

1. fetch or derive context
2. build prompt
3. call `openclaw agent`
4. save artifacts
5. parse sections
6. build Feishu card payloads
7. send or skip with an explicit reason

The current app entrypoint is `tools/firststand_feishu_digest.py`.

### 4. Validate narrow to broad

Always validate in this order:

1. local preview without sending
2. inspect generated text and context artifacts
3. one real Feishu send if the feature affects delivery
4. deploy to the VPS
5. one narrow live verification on the VPS

Do not claim success from code inspection alone.

## Working Rules

- Source live values from the project root `.env`; do not reintroduce raw secrets into skill docs or code comments.
- Patch local source first, then copy to the VPS.
- When adding sections, update the parser-facing title lists as well as the prompt text.
- When adding data, update the context builder before expanding the prompt.
- When adding delivery or dedupe behavior, inspect the current state files under `/var/lib/openclaw-firststand` before inventing new ones.
- Current Feishu delivery is custom-bot webhook mode; do not promise stable inline uploaded images unless the bot model itself changes.

## What To Read

- `references/feature-map.md`: feature types → code touchpoints
- `references/validation-loop.md`: local preview, send, deploy, and artifact checks
