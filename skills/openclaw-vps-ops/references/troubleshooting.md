# Notifier And Adjacent Troubleshooting

Use this file only after `openclaw-diagnostics.md` shows that OpenClaw core is healthy.

If the symptom is really about SSH/login, host networking, disk, memory, or generic scheduler/service failures, switch to `$vps-incident-diagnostics` first.

## 1. Default evidence pack

Start with this evidence before editing code:

```bash
/Users/fint/Public/projects/wint/skills/openclaw-vps-ops/scripts/collect_vps_snapshot.expect
ls -lt /var/lib/openclaw-firststand | head -n 20
ls -l /var/log/openclaw-firststand.log /var/log/openclaw-firststand-prematch.log
```

Then inspect the newest state artifacts that match the symptom.

## 2. Symptom guide

### A. Daily digest did not send

Checks:

```bash
sed -n '1,120p' /etc/cron.d/openclaw-firststand-feishu
sed -n '1,120p' /usr/local/bin/openclaw-firststand-feishu
sed -n '1,120p' /etc/openclaw-firststand.env
ls -lt /var/lib/openclaw-firststand | head -n 20
ls -l /var/log/openclaw-firststand.log
```

Manual validation:

```bash
set -a
. /etc/openclaw-firststand.env
set +a
/opt/openclaw-firststand/firststand_feishu_digest.py --send
```

Likely causes:

- cron did not fire
- env file is missing or malformed
- remote deployed script is stale versus local source
- OpenClaw core passed earlier checks but the actual model call still failed
- Feishu webhook delivery failed

### B. LPL prematch reminder did not send

Checks:

```bash
sed -n '1,120p' /usr/local/bin/openclaw-firststand-prematch
sed -n '1,120p' /etc/openclaw-firststand.env
cat /var/lib/openclaw-firststand/prematch_sent.json
sed -n '1,220p' /var/lib/openclaw-firststand/last_prematch_context.json
ls -l /var/log/openclaw-firststand-prematch.log
```

Manual validation:

```bash
set -a
. /etc/openclaw-firststand.env
set +a
/opt/openclaw-firststand/firststand_feishu_digest.py --send-prematch
```

If you need to simulate a specific future window, add `--datetime 2026-03-10T12:00:00+08:00` or another exact ISO timestamp.

Likely causes:

- target match is outside `PREMATCH_ALERT_WINDOW_HOURS`
- dedupe entry already exists in `prematch_sent.json`
- official schedule is still `TBD` and fallback pairing logic no longer matches external sources
- the local file was patched but the remote deployed copy was not

### C. Daily cards are too big, split incorrectly, or section content looks wrong

Inspect these first:

```bash
sed -n '1,260p' /var/lib/openclaw-firststand/last_digest.txt
sed -n '1,260p' /var/lib/openclaw-firststand/last_digest_context.json
```

Then compare local and remote code:

```bash
wc -c /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py
ssh -p "${VPS_PORT:-22}" "${VPS_USER}@${VPS_HOST}" 'wc -c /opt/openclaw-firststand/firststand_feishu_digest.py'
```

Likely causes:

- digest splitting logic differs between local and deployed copies
- OpenClaw generated malformed section boundaries
- the context file already contains bad source data, so rendering is only the downstream symptom

### D. LPL news, pairing inference, or 晋级分析 looks off

Inspect these first:

```bash
sed -n '1,220p' /var/lib/openclaw-firststand/last_prematch.txt
sed -n '1,260p' /var/lib/openclaw-firststand/last_prematch_context.json
sed -n '1,260p' /var/lib/openclaw-firststand/last_digest_context.json
```

Likely causes:

- source page structure changed
- official `lolesports` event order changed
- news normalization pulled the wrong items
- fallback inference is still being used when official data became available

### E. Feishu sends but inline images are missing

This is expected with the current setup.

Current state:

- delivery uses a Feishu custom-bot webhook
- no app credentials or `img_key` upload flow is configured
- interactive cards can carry links cleanly, but stable inline news images are not wired up yet

Do not treat this as a notifier bug unless the user explicitly wants to upgrade to a full Feishu app bot.

### F. `CLIProxyAPI` is installed but not usable

Checks:

```bash
/usr/local/bin/CLIProxyAPI --version
ps -ef | grep -i cli-proxy-api | grep -v grep
find /etc/cliproxyapi /opt/cliproxyapi -maxdepth 3 \( -name 'config*.yaml' -o -name 'config*.yml' \)
```

Current likely explanation:

- binary is installed
- no canonical live config is wired in
- no service is running

Treat `CLIProxyAPI` as a separate follow-up project unless the user explicitly asks for it to be configured.

## 3. Safe deployment loop for notifier changes

Local → remote pattern:

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a

scp -P "${VPS_PORT:-22}" /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py \
  "${VPS_USER}@${VPS_HOST}:/opt/openclaw-firststand/firststand_feishu_digest.py"

ssh -p "${VPS_PORT:-22}" "${VPS_USER}@${VPS_HOST}" 'chmod 755 /opt/openclaw-firststand/firststand_feishu_digest.py && python3 -m py_compile /opt/openclaw-firststand/firststand_feishu_digest.py'
```

Then run the narrowest wrapper or direct script command needed to verify the exact change.

## 4. Secret handling rules

Live values now live in the project root `.env`, which is gitignored.

Reference docs:

- host access key names: `/Users/fint/Public/projects/wint/skills/vps-incident-diagnostics/references/live-access.md`
- app-level key names: `references/live-secrets.md`

Still avoid dumping fresh raw secret-bearing files into new docs or normal chat replies:

- `/root/.openclaw/openclaw.json`
- `/root/.config/systemd/user/openclaw-gateway.service`
- `/etc/openclaw-firststand.env`
- `/Users/fint/Public/projects/wint/playground/codex-5d358b1d-simonettasillavanjt466@gmail.com-team (1).json`

Prefer reporting:

- file exists / missing
- size / mtime
- redacted keys
- service status
