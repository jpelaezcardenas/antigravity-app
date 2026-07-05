## Context

A read-only audit of the GBrain adoption (`adopt-gbrain-second-brain`) surfaced five findings. Immediate containment for the two urgent ones has already been applied directly (not part of this OpenSpec change's task list, since they were operational/config actions, not code):

- `DEMO_AUTH_ENABLED=False` set on Railway production and redeployed; verified live — the demo-admin login now returns "Credenciales inválidas".
- `gbrain-autopilot.service` restarted in WSL; confirmed `active (running)`.
- `/home/contexia/gbrain/.env` permissions fixed to `600`.
- `C:\Users\contexia\.gbrain\config.json` (the Windows-side GBrain clone) deleted outright — confirmed unused, since all Claude Code/Codex/Hermes work already goes through the WSL install.

This design covers the remaining **durable** fixes: removing the committed secret from source, hardening the autopilot service's restart policy so the underlying crash (a GBrain-internal `config.poolSize` bug on DB reconnect) self-heals without a human restarting it, and documenting the upstream-drift risk in the GBrain clone.

## Goals / Non-Goals

**Goals:**
- No secret value (password, API key, connection string) exists in git-tracked source going forward.
- `gbrain-autopilot.service` recovers automatically from the known `config.poolSize` crash without manual intervention.
- The `manifest.json`/`RESOLVER.md` upstream-drift trade-off (already accepted in the original adoption's design) has a documented, repeatable re-apply procedure.
- `ARCHITECTURE.md` reflects the current, corrected state (no stale claims about a Windows-side install or an unhardened restart policy).

**Non-Goals:**
- Patching GBrain's own compiled binary to fix the `config.poolSize` bug — it's Garry Tan's upstream code; the mitigation is the restart policy, not a patch.
- Rewriting git history to purge the old leaked password commit. The password is being rotated (a separate, manual, out-of-band action by the founder); once rotated, the old committed value is inert. Rewriting shared git history has its own risks (force-push, collaborator breakage) that aren't justified once the credential itself is dead.
- Building a general secrets-management layer for the backend. This change only removes the one hardcoded value found; broader secret-handling hygiene (e.g. moving all Railway env vars into Bitwarden Secrets Manager) is already tracked separately.

## Decisions

**D1 — Demo password via environment variable, not deletion of the feature.** `DEMO_AUTH_ENABLED` and a new `DEMO_ADMIN_PASSWORD` env var replace the hardcoded value. Alternative considered: delete the demo-admin account entirely. Rejected because the founder still uses it for MVP demos; the fix is "never hardcode a real secret," not "remove the convenience feature." `cliente@demo.co` / `"demo"` stays hardcoded since it is not a real credential (a throwaway demo password for a fictitious client, not tied to any real system).

**D2 — `Restart=always` over patching the crash.** GBrain's autopilot exits with code 0 after "5 consecutive worker crashes, giving up" — a deliberate self-imposed circuit breaker inside GBrain itself, not a systemd-visible failure. `Restart=on-failure` only restarts on non-zero exit; `Restart=always` restarts regardless of exit code, which is what's needed here since the process's own internal giving-up looks like success to systemd. Alternative considered: `RestartForceExitStatus=0` (surgical, only forces restart on that one exit code) — rejected as needlessly narrow; if GBrain's exit codes change in a future upstream version, `Restart=always` degrades gracefully while a hardcoded exit-status list would silently stop working.

**D3 — Runbook, not automation, for CFG-1.** The `manifest.json`/`RESOLVER.md` drift only needs to be re-applied after an explicit `git pull` in the GBrain clone, which is an infrequent, human-initiated action. A documented one-command runbook step (`python scripts/generate_gbrain_skills.py`) is sufficient; building a git-hook or CI check for a personal WSL clone that isn't part of any repo's CI is over-engineering for the actual frequency of this event.

## Risks / Trade-offs

- **[Risk]** `Restart=always` could mask a genuine, unrelated future crash loop (e.g. a real bug introduced by Contexia's own config) by restarting forever instead of surfacing the failure. → **Mitigation:** systemd's own `StartLimitIntervalSec`/`StartLimitBurst` (already implicitly bounded by systemd defaults) still caps restart frequency; if it becomes chronically noisy, that's visible via `systemctl --user status` showing high restart counts, which is the same signal used to catch RUN-1 in the first place.
- **[Risk]** Setting `DEMO_ADMIN_PASSWORD` via Railway still puts a real secret in a third-party platform's env var store (not git, but not a secrets manager either). → **Mitigation:** out of scope for this change (see Non-Goals); tracked separately as the Bitwarden Secrets Manager migration.
- **[Risk]** If the password rotation (manual, by the founder) hasn't happened by the time this change deploys, the old leaked value is still technically valid at whatever system uses that Bitwarden master password. → **Mitigation:** this is independent of code deploy timing — flagged as the single highest-priority manual action, not gated on this OpenSpec change's completion.

## Migration Plan

1. Code change: `auth_service.py` reads `settings.DEMO_ADMIN_PASSWORD` instead of a literal string; `config.py` adds the setting (empty-string default, so demo login silently fails closed if unset rather than falling back to a hardcoded value).
2. Set `DEMO_ADMIN_PASSWORD` on Railway production (a new value, not the leaked one) — done as part of Stage 11 deploy, not before, so the literal string is removed from source in the same commit that makes the feature functional again.
3. Edit `gbrain-autopilot.service` unit file in WSL directly (`~/.config/systemd/user/gbrain-autopilot.service`), `systemctl --user daemon-reload`, restart, verify.
4. Add the runbook section to `docs/gbrain-adoption.md`.
5. Update `ARCHITECTURE.md` Decisiones asentadas.
6. Rollback: reverting the `auth_service.py` commit would restore hardcoded-password behavior — not a real rollback path given the security fix is the point; if the env-var approach breaks demo login, the fix-forward is setting the Railway var correctly, not reverting.

## Open Questions

None — scope is fully bounded by the audit's five findings, two of which are already resolved via direct containment (documented above, outside this change's task list since no code/spec artifact needed changing for them).
