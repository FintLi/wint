# OpenClaw Core Diagnostics

Use this file after reading `deployment-map.md`. It assumes the VPS itself is reachable and healthy enough to run app-level checks.

If you cannot log in, DNS is broken, disk is full, memory is exhausted, or generic services are failing, switch to `$vps-incident-diagnostics` first.

## 1. First checks

Before editing anything, re-run `scripts/collect_vps_snapshot.expect` or run these commands on the VPS:

```bash
export XDG_RUNTIME_DIR=/run/user/0
command -v openclaw
openclaw --version
systemctl --user status openclaw-gateway --no-pager
journalctl --user -u openclaw-gateway -n 80 --no-pager
ss -ltnp | grep ':18789' || true
find /root/.openclaw -maxdepth 2 -type f | sort
ls -l /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak
```

Read this packet as one unit:

- missing binary usually means install or PATH drift
- inactive gateway usually means service, token, or auth trouble
- no listener on `18789` means the gateway is not actually serving
- missing `openclaw.json` means auth/config drift until proven otherwise

## 2. Minimal agent probe

Use the same command shape as the notifier's `run_openclaw()` implementation:

```bash
openclaw agent --agent main --message 'Reply with OK only.' --thinking low --json
```

Expected result:

- command exits `0`
- stdout is valid JSON
- `result.payloads[].text` contains at least one non-empty text item

If the live agent name may differ, read `OPENCLAW_AGENT` from `/etc/openclaw-firststand.env` and repeat the probe with that value.

If the CLI exits non-zero or the JSON payload is empty, the problem is still OpenClaw core. Do not jump into Feishu or content debugging yet.

## 3. Symptom buckets

### A. Binary missing or wrong version

Checks:

```bash
command -v openclaw
openclaw --version
```

Likely causes:

- failed or partial upgrade
- binary replaced but service still points at old runtime assumptions
- PATH drift in the interactive shell versus the user service

Fix focus:

- restore a working `openclaw` binary first
- then re-run the minimal agent probe before touching notifier code

### B. Gateway service is down or flapping

Checks:

```bash
export XDG_RUNTIME_DIR=/run/user/0
systemctl --user cat openclaw-gateway
systemctl --user restart openclaw-gateway
systemctl --user status openclaw-gateway --no-pager
journalctl --user -u openclaw-gateway -n 120 --no-pager
ss -ltnp | grep ':18789' || true
```

Likely causes:

- bad token or environment in the unit file
- version drift created an incompatible launch path
- user-service state is stale and needs reload/restart

Fix focus:

- correct the unit or token source
- run `systemctl --user daemon-reload` if the unit changed
- restart the service and confirm port `18789` is listening

### C. Auth or config drift under `/root/.openclaw`

Checks:

```bash
ls -la /root/.openclaw
stat -c '%n %s %y' /root/.openclaw/openclaw.json /root/.openclaw/openclaw.json.bak
```

Likely causes:

- `openclaw.json` missing or replaced
- stale backup restored without verifying freshness
- permission or ownership drift under `/root/.openclaw`

Recovery notes:

- load `/Users/fint/Public/projects/wint/.env` for current host and app secret values
- `references/live-secrets.md` documents the relevant environment key names
- `OPENAI_AUTH_JSON_PATH` is local input material, not remote truth

### D. Agent probe fails even though the gateway looks healthy

Checks:

```bash
set -a
. /etc/openclaw-firststand.env
set +a
openclaw agent --agent "${OPENCLAW_AGENT:-main}" --message 'Reply with OK only.' --thinking low --json
```

Likely causes:

- notifier is using a different agent name than your manual probe
- gateway is reachable but auth/session state is still invalid
- CLI returns JSON with no text payload, which breaks downstream parsing

Fix focus:

- make the manual probe match the notifier env exactly
- inspect gateway logs before changing notifier parsing
- compare results with the expectation in `/Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py`

### E. Version drift is visible but behavior is not clearly broken

Current known fact:

- runtime observed on 2026-03-09: `2026.3.2`
- gateway logs advertised: `2026.3.7` available

Rule:

- do not upgrade during a notifier/content incident unless the current runtime is the proven root cause
- snapshot first, record the old version, update the binary, restart the gateway, and re-run the minimal probe before testing downstream layers

## 4. Handoff to downstream troubleshooting

Only move to `troubleshooting.md` when all of the following are true:

- gateway is active and listening on `18789`
- a minimal `openclaw agent` probe succeeds
- auth files exist and look current enough to use
- the failure reproduces in wrappers, cron, Feishu cards, state files, or `CLIProxyAPI`
