# Stage 11 — Deployment report (2026-09-09)

**Status: DEPLOYED AND VERIFIED.**

## Merge and deploy

| | |
|---|---|
| Merged | `1bfa866..bb1ea1f` → `main`, fast-forward (no merge commit) |
| Pushed | `origin/main` |
| Railway | deployment `2d4abd71-5852-494d-a9c0-4e7067dc118e`, **SUCCESS** |
| No migration | this change touches no schema |
| No frontend build | no `contexia-app/` file was modified — confirmed via `git status --short` before committing (only `ARCHITECTURE.md`, `docs/pricing.md`, and files under `apps/backend/`) |

## Verified live

| Route | Result |
|---|---|
| `/api/v1/health` | 200 |
| `/api/v1/pricing/pre-cotizacion` | 401 (mounted, auth enforced — unaffected by this change) |
| `/api/v1/financials` | 401 (unaffected) |
| `/api/v1/agents/ask` | 401 (Taty's own endpoint — unaffected) |

## Honest limit of this verification

HTTP status codes confirm the backend redeployed successfully with the new commit and that
nothing crashed. They do **not** confirm the prompt text itself is what a real WhatsApp
conversation sees — that requires either an authenticated conversation (this agent does not
handle plaintext credentials) or trusting that the deployed commit matches what was tested.

What is verifiable and was verified: the deployed Railway build is `2d4abd71`, built from the
commit that fast-forwarded `main` to `bb1ea1f`, which is the exact commit whose 66 new tests
(catalog + prompt-construction, run locally against the real `core/pricing_catalog.py` and
`TatyAgentService._build_system_prompt`) passed before merge. Nothing was hand-edited on the
server side, and no separate build step exists for the backend to diverge from what was
committed (unlike the frontend's static-export gap this repo has hit before).

**Founder action, not blocking**: send Taty a real WhatsApp message asking "¿cuánto cuesta
declarar renta?" and confirm she states "desde $350.000" with the three drivers, and does not
invent an exact final number. Same pattern as every prior tenant-scoped change's deferred
live-login verification.
