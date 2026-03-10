# VPS Symptom Runbook

Use this file after collecting a fresh host snapshot.

## 1. Cannot SSH into the VPS

Load the project root `.env`, then check from the client side first:

```bash
set -a
. /Users/fint/Public/projects/wint/.env
set +a
ssh -p "${VPS_PORT:-22}" "${VPS_USER}@${VPS_HOST}"
nc -vz "$VPS_HOST" "${VPS_PORT:-22}"
```

Once inside or via an alternate console, inspect:

```bash
systemctl status ssh
ss -ltnp | grep ':22 '
grep -E '^(Port|PermitRootLogin|PasswordAuthentication)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null
journalctl -u ssh -n 100 --no-pager
```

Likely causes:

- SSH daemon down
- SSH not listening on expected port
- root login or password auth disabled
- firewall blocking `22`

## 2. VPS is slow, laggy, or timing out

Check:

```bash
uptime
free -h
vmstat 1 5
ps aux --sort=-%mem | head -n 20
ps aux --sort=-%cpu | head -n 20
df -hT
df -ih
```

Likely causes:

- RAM exhaustion and swap thrash
- a runaway process
- disk or inode exhaustion
- CPU saturation

## 3. A port should be open but is not reachable

Check:

```bash
ss -ltnup
ip addr
ip route
nft list ruleset 2>/dev/null || true
iptables -S 2>/dev/null || true
ufw status 2>/dev/null || true
```

Likely causes:

- service not listening
- wrong bind address
- firewall or nftables rules
- routing or interface issue

## 4. Scheduled jobs did not run

Check both cron and systemd timer surfaces:

```bash
systemctl list-timers --all
ls -l /etc/cron.d
crontab -l
journalctl -u cron -n 100 --no-pager 2>/dev/null || journalctl -u crond -n 100 --no-pager 2>/dev/null
```

On this host, also inspect:

```bash
sed -n '1,120p' /etc/cron.d/openclaw-firststand-feishu
ls -lt /var/lib/openclaw-firststand | head -n 20
```

Likely causes:

- malformed cron file
- environment not loaded in wrapper
- target script failing silently
- system time / timezone confusion

## 5. A service keeps failing or restarting

Check:

```bash
systemctl --failed
journalctl -p err -n 120 --no-pager
systemctl status <unit>
journalctl -u <unit> -n 200 --no-pager
```

If it is a user service, use:

```bash
systemctl --user status <unit>
journalctl --user -u <unit> -n 200 --no-pager
```

On this VPS, important examples are:

- `openclaw-gateway.service` (user service)
- `wireproxy.service`

## 6. DNS or outbound requests are failing

Check:

```bash
cat /etc/resolv.conf
getent hosts openai.com
getent hosts open.feishu.cn
curl -I https://api.openai.com 2>/dev/null | head -n 5 || true
curl -I https://open.feishu.cn 2>/dev/null | head -n 5 || true
```

Likely causes:

- broken resolver
- upstream network issue
- local firewall / proxy interference

## 7. Host is healthy but app is broken

At this point, hand off:

- OpenClaw-specific issues → `skills/openclaw-vps-ops`
- notifier content / Feishu issues → `skills/openclaw-vps-ops`
- CLIProxyAPI config issues → start here for host checks, then continue in `skills/openclaw-vps-ops` because that skill already documents its install details

## 8. Highest-value command bundle

When you need a fast triage pass, these usually give the answer quickly:

```bash
uptime
free -h
df -hT
df -ih
systemctl --failed
ss -ltnup
ps aux --sort=-%mem | head -n 15
ps aux --sort=-%cpu | head -n 15
journalctl -p err -n 80 --no-pager
```
