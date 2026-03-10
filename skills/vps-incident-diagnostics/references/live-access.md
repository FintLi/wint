# VPS Access Environment Keys

Actual live login values now live in the project root `.env`, which is intentionally gitignored.

Load it before running connection or snapshot commands:

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a
```

Relevant keys:

- `VPS_HOST`
- `VPS_PORT`
- `VPS_USER`
- `VPS_PASSWORD`

Related app-level values are documented by key name in `/Users/fint/Public/projects/wint/skills/openclaw-vps-ops/references/live-secrets.md`.
