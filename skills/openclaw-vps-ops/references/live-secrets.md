# App Environment Keys

Actual live app secrets now live in the project root `.env`, which is intentionally gitignored.

Load it before running app-level probes or deployment commands:

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a
```

## VPS access keys

- `VPS_HOST`
- `VPS_PORT`
- `VPS_USER`
- `VPS_PASSWORD`

## Feishu keys

- `FEISHU_WEBHOOK`

## OpenClaw gateway keys

- `OPENCLAW_GATEWAY_PORT`
- `OPENCLAW_GATEWAY_TOKEN`
- `OPENCLAW_GATEWAY_SERVICE_FILE`

## Local auth input

- `OPENAI_AUTH_JSON_PATH`

The skill docs should reference these key names or the root `.env` path, not paste raw values.
