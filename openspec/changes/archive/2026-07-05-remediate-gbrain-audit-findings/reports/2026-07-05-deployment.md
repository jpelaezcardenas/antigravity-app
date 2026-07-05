# Deployment Report — remediate-gbrain-audit-findings (2026-07-05)

## Summary

Remediated all five findings from the post-adoption GBrain audit: a dead autopilot service
with an inadequate restart policy, a plaintext production credential exposed via an unused
Windows-side GBrain clone, world-writable/loose file permissions, undocumented upstream drift
in the GBrain clone's skill projection, and — found incidentally, unrelated to GBrain — a
hardcoded real credential (the Bitwarden master password) live as a demo-admin login password
in production.

## Immediate containment (applied directly, verified live, before this change's artifacts existed)

| Action | Verification |
|---|---|
| `DEMO_AUTH_ENABLED=False` set on Railway production, redeployed | Live login POST with the leaked password returned `{"detail":"Credenciales inválidas"}` |
| `gbrain-autopilot.service` restarted (WSL) | `systemctl --user status` → `active (running)` |
| `/home/contexia/gbrain/.env` → `chmod 600` | `ls -la` confirmed `-rw-------` |
| `C:\Users\contexia\.gbrain\config.json` deleted | Confirmed unused (WSL is sole GBrain install); file removed |

## Durable fixes (this change)

| Task | Result |
|---|---|
| 1. Hardcoded password removed from `auth_service.py` | `DEMO_ADMIN_PASSWORD` env var (empty default, fails closed); `grep -rn "Lindafea0712" apps/backend/` clean |
| 2. Autopilot restart policy hardened | `Restart=always` in `gbrain-autopilot.service`; verified by `kill -9`ing the worker — systemd auto-restarted it (`Result: signal`, the exact exit mode the old `on-failure` policy missed). Hit GBrain's own stale lock file as a side effect of the SIGKILL test; removed the stale lock (PID confirmed dead first) and the service settled into clean `active (running)` |
| 3. CFG-1 runbook | Added to `docs/gbrain-adoption.md`: "Runbook: re-applying the Contexia skill projection after a GBrain upstream pull" + "Restart policy" sections |
| 4. Canon docs updated | `ARCHITECTURE.md` Decisiones asentadas #10 extended, new #11 added |
| 5. Stage 11 | Commit `af6a769` pushed to `main`; Railway auto-deployed |

## Founder decision on demo-admin password

Left `DEMO_ADMIN_PASSWORD` unset and `DEMO_AUTH_ENABLED=false` in production — the demo-admin
login stays disabled until explicitly reactivated later with a newly generated password. No
new secret was introduced.

## Production verification (post-deploy)

- Deploy `86309c58` (commit `af6a769`): SUCCESS.
- Demo-admin login (old leaked password `Lindafea0712`): rejected in production — see live
  verification below.
- Demo-admin login (any password, `DEMO_AUTH_ENABLED=false`): rejected — consistent with intended
  disabled state.

## Manual action still pending (tracked, not blocking this change)

- **Bitwarden master password rotation** — flagged as the single highest-priority action,
  owned by the founder, independent of this change's deploy timing. The code-level fix (no
  hardcoded value, disabled by default) closes the *reachable* exploit path regardless of
  whether the underlying Bitwarden password has been rotated yet.

## Files changed

- `apps/backend/config.py` — added `DEMO_ADMIN_PASSWORD` setting
- `apps/backend/application/auth_service.py` — reads password from settings, fails closed on empty
- `~/.config/systemd/user/gbrain-autopilot.service` (WSL, not in this repo) — `Restart=always`
- `docs/gbrain-adoption.md` — runbook + restart policy documentation
- `ARCHITECTURE.md` — Decisiones asentadas #10/#11
