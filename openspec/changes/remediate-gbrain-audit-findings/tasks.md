## 0. Already Completed (Immediate Containment — Direct Actions, Not OpenSpec-Gated)

These were executed directly with founder approval before this change's artifacts existed, since they were reversible operational/config actions, not code:

- [x] 0.1 Set `DEMO_AUTH_ENABLED=False` on Railway production (`elegant-success`), redeployed, verified live via a real login POST returning "Credenciales inválidas" for the leaked demo-admin password.
- [x] 0.2 Restarted `gbrain-autopilot.service` in WSL; confirmed `active (running)`.
- [x] 0.3 `chmod 600 /home/contexia/gbrain/.env`.
- [x] 0.4 Deleted `C:\Users\contexia\.gbrain\config.json` (Windows-side GBrain install, confirmed unused).
- [ ] 0.5 (Manual, founder-only, tracked here for visibility — not verifiable by an agent) Rotate the Bitwarden master password that was hardcoded in `auth_service.py`.

## 1. Remove Hardcoded Demo Password from Source

- [x] 1.1 Add `DEMO_ADMIN_PASSWORD: str = ""` to `apps/backend/config.py` (empty-string default — fails closed if unset).
- [x] 1.2 In `apps/backend/application/auth_service.py`, replace the literal `"password": "Lindafea0712"` value for `contexia.marketing@gmail.com` with `settings.DEMO_ADMIN_PASSWORD`, and add a check that rejects the login if `settings.DEMO_ADMIN_PASSWORD` is empty (so an unset env var fails closed rather than matching an empty string).
- [x] 1.3 Confirm `cliente@demo.co` / `"demo"` is left as-is (not a real secret, per design D1).
- [x] 1.4 `grep -rn "Lindafea0712" apps/backend/` returns no matches after the edit (a stale, gitignored `__pycache__/*.pyc` initially matched — cleaned; never committed).

## 2. Harden Autopilot Restart Policy

- [x] 2.1 Edit `~/.config/systemd/user/gbrain-autopilot.service` in WSL: change `Restart=on-failure` to `Restart=always`.
- [x] 2.2 `systemctl --user daemon-reload && systemctl --user restart gbrain-autopilot.service`; confirm `active (running)`.
- [x] 2.3 Verification: `kill -9` the worker PID — systemd auto-restarted it (`Result: signal`, the exact exit mode the old policy missed). The restart initially hit GBrain's own stale lock file (left by the SIGKILL not cleaning up `~/.gbrain/autopilot.lock`); removed the stale lock (PID confirmed dead first) and the service settled into `active (running)` on the next `RestartSec=30` cycle — confirming the crash-loop now self-heals instead of giving up permanently.

## 3. Document CFG-1 Runbook

- [x] 3.1 Added "Runbook: re-applying the Contexia skill projection after a GBrain upstream pull" and "Restart policy" sections to `docs/gbrain-adoption.md`.

## 4. Update Canon Docs

- [x] 4.1 Updated `ARCHITECTURE.md` "Decisiones asentadas": #10 extended (autopilot `Restart=always`, Windows-side GBrain install removed) and new #11 added (demo auth env-gated, no hardcoded secret).

## 5. Stage 11 — Deploy to Production (MANDATORY)

See `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`.

- [x] 5.1 Founder decision: leave `DEMO_ADMIN_PASSWORD` unset and `DEMO_AUTH_ENABLED=false` in production for now — demo login stays disabled until explicitly reactivated with a new password later. No value set.
- [ ] 5.2 `git commit` + push to `main`.
- [ ] 5.3 Railway deploy active (backend change) — confirm green.
- [ ] 5.4 Verify in production: demo-admin login attempt (any password) is rejected while `DEMO_AUTH_ENABLED=false`.
- [ ] 5.5 Verify in production: the old leaked password (`Lindafea0712`) is rejected.
- [ ] 5.6 Create report: `openspec/changes/remediate-gbrain-audit-findings/reports/YYYY-MM-DD-deployment.md`.
