# Design: houston-lead-scoring-read-only-bridge

## Context

The master plan's Subdomain 7 (`houston-outreach-content-critic-bridge`) was scoped as an
investigation with an explicit fork: either generalize `sell_machine_service.py::run_creative_loop`
(rename `manus_draft_hooks` → a more generic `external_draft_hooks`) to accept Houston-produced
outreach hooks, or build a parallel validation flow, depending on what shape Houston's outreach
agent actually produces. Investigation confirmed Houston ships as closed compiled binaries
(`houston-app.exe`/`houston-engine.exe`, no source, no config schema locally inspectable) — its
real output shape could not be determined by reading code.

## Decision D1 — Neither fork applies: Houston is read-only lead-scoring, not outreach generation

The founder's own decision (documented in `docs/integrations/houston-plan-integracion.md`,
produced in a separate session with direct knowledge of Houston's actual configuration) resolves
this more simply than either originally-proposed fork: Houston is being used **read-only, for
lead-scoring and pipeline visibility**, connecting to Contexia's existing HubSpot portal
(`51867201`) via its own Composio connector — the same portal `hermes-hubspot-poller` already
writes to unidirectionally. Houston never writes back to HubSpot, and its 18 sales skills are not
being used to generate content that would need Content Critic validation at this time ("por ahora
autotag only").

**Consequence**: no generalization of `run_creative_loop`/`manus_draft_hooks` is needed. The
Approval Queue and Content Critic loop remain exactly as `crm-alta-tiered-provisioning` and the
other subdomains left them — untouched by this investigation.

## Decision D2 — Persist the two artifacts as durable repo docs, not scratch/session output

The plan's own original draft (in `houston-plan-integracion.md`'s "Files to create" section)
suggested the playbook file should live only in a session scratchpad, downloaded by the founder
and uploaded to Houston, never committed. The founder explicitly overrode this: "deben quedar como
fuente fija acá, no perdidos en un hilo de Claude Code." Both documents are committed to
`docs/integrations/` as the canonical, durable record of this integration decision — matching the
repo's existing pattern of `docs/*-standards.md` for durable reference material that isn't code.

## Decision D3 — The excluded third document (API-key troubleshooting) stays excluded

The founder deliberately excluded a third source document (MiMo/Xiaomi API key troubleshooting)
from what gets persisted — it contained exposed `sk-`/`tp-` keys and is a one-off support
conversation, not permanent sales/integration knowledge. This change does not re-introduce it.
**Follow-up flagged, not resolved here**: if those keys have not yet been rotated from the Xiaomi
MiMo console, that remains an outstanding founder action, independent of this change.

## Out of scope

- Building any pipeline for Chatwoot's lead-classification tags (intención/prioridad/
  servicio_interes) to reach HubSpot so Houston could see them — explicitly deferred as a future,
  separate change if the founder decides the value justifies it. Chatwoot is not in Houston's
  Composio connector list today.
- Rotating the MiMo/Xiaomi API keys — a founder action outside this repo, mentioned for
  completeness only.
- Any change to `hermes-hubspot-poller` or the HubSpot sync contract itself
  (`hubspot-sync-renta-natural`, ARCHITECTURE.md Decision #20) — unchanged, unidirectional,
  already correct for Houston's read-only use case.
