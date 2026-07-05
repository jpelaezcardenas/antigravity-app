## Why

A read-only audit of the GBrain adoption (`adopt-gbrain-second-brain`, archived 2026-07-05) found five live issues, re-verified directly before writing this proposal: the WSL autopilot service crash-loops and gives up on a transient network blip because `Restart=on-failure` doesn't cover its clean-exit failure mode; the Windows-side GBrain clone held a plaintext production DB credential at world-writable permissions (already deleted as an immediate containment step, since it was confirmed unused); and — found incidentally during the same secret sweep, unrelated to GBrain itself — `auth_service.py` hardcodes the real Bitwarden master password as a demo-admin login password, which was live and reachable in production (confirmed via Railway: `DEMO_AUTH_ENABLED` was unset, defaulting to `true`). The env var has been flipped to `false` as immediate containment; this change makes that fix durable and removes the committed secret from source.

## What Changes

- Harden `gbrain-autopilot.service`: `Restart=on-failure` → `Restart=always`, so a clean-exit crash-loop (the `config.poolSize` reconnect bug) still recovers without manual intervention.
- Document the CFG-1 upstream-drift risk (`skills/manifest.json` / `skills/RESOLVER.md` locally modified in the GBrain clone) with a runbook for re-applying `scripts/generate_gbrain_skills.py` after a `git pull`.
- Remove the hardcoded demo-admin password from `apps/backend/application/auth_service.py`; load it from an environment variable instead, set via Railway (never committed). `DEMO_AUTH_ENABLED` stays env-controlled (already flipped to `false` in production as immediate containment) rather than defaulting to `true` in code.
- Update `ARCHITECTURE.md` "Decisiones asentadas" recording: autopilot restart policy hardened, Windows-side GBrain install removed (confirmed unused), demo auth now secret-free and env-gated with a safe default.

## Capabilities

### New Capabilities
- `auth-demo-credentials`: demo/admin login credentials must never be hardcoded in source and must default to disabled unless explicitly enabled via environment configuration. No existing spec governs backend auth secret handling, and this is unrelated to GBrain, so it gets its own capability rather than being folded into `gbrain-adoption`.

### Modified Capabilities
- `gbrain-adoption`: adds a restart-policy requirement for the autopilot service and a runbook requirement for the skills-projection upstream-drift risk.

## Impact

- `apps/backend/application/auth_service.py`, `apps/backend/config.py` (`DEMO_AUTH_ENABLED` default)
- `~/.config/systemd/user/gbrain-autopilot.service` (WSL)
- `docs/gbrain-adoption.md` (new runbook section)
- `ARCHITECTURE.md` (Decisiones asentadas)
- Railway production env vars (`DEMO_AUTH_ENABLED`, new `DEMO_ADMIN_PASSWORD`)
