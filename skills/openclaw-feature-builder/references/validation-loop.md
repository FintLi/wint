# Validation Loop

Use this loop whenever a feature is added or modified.

## 1. Load live values

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a
```

## 2. Local preview first

Digest preview without sending:

```bash
python3 /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py \
  --datetime 2026-03-10T09:00:00+08:00
```

Prematch preview or real-path simulation:

```bash
python3 /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py \
  --send-prematch \
  --datetime 2026-03-10T12:00:00+08:00
```

If you do not want a real send while testing prematch behavior, patch the feature behind the narrowest branch possible first and inspect the generated artifacts before widening validation.

## 3. Artifact checks

Inspect the newest evidence under:

- `/var/lib/openclaw-firststand/last_digest_context.json`
- `/var/lib/openclaw-firststand/last_digest.txt`
- `/var/lib/openclaw-firststand/last_prematch_context.json`
- `/var/lib/openclaw-firststand/last_prematch.txt`
- `/var/lib/openclaw-firststand/prematch_sent.json`

Use these to distinguish:

- bad source/context
- bad prompt output
- bad card parsing/rendering
- bad dedupe/send behavior

## 4. One real send when needed

Digest:

```bash
python3 /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py \
  --send \
  --datetime 2026-03-10T09:00:00+08:00
```

Prematch:

```bash
python3 /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py \
  --send-prematch \
  --datetime 2026-03-10T12:00:00+08:00
```

## 5. Deploy only after local proof

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a

scp -P "${VPS_PORT:-22}" /Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py \
  "${VPS_USER}@${VPS_HOST}:/opt/openclaw-firststand/firststand_feishu_digest.py"

ssh -p "${VPS_PORT:-22}" "${VPS_USER}@${VPS_HOST}" \
  'chmod 755 /opt/openclaw-firststand/firststand_feishu_digest.py && python3 -m py_compile /opt/openclaw-firststand/firststand_feishu_digest.py'
```

## 6. Narrow live verification

Choose the narrowest live command that proves the feature:

- preview-only logic → run the script once without `--send`
- digest delivery change → run one `--send`
- prematch logic → run one `--send-prematch` with an exact `--datetime`
- schedule change → inspect the remote cron file and run one manual invocation

## 7. Done criteria

Do not say the feature is complete until all relevant checks pass:

- local code runs
- generated artifacts match the feature intent
- Feishu card layout or content is correct if delivery changed
- remote deployed file is updated and compiles
- one live verification succeeds on the VPS
