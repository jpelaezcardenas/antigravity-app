## ADDED Requirements

### Requirement: The telemetry-aware creative loop is reachable via an endpoint
The system SHALL expose `POST /api/v1/sell-machine/creative-loop/run`, which SHALL call
`run_creative_loop(count, target_segment, use_telemetry=True)` and return the surviving hooks.
This is the only way the telemetry-aware loop runs in production — Hermes (the local orchestrator
that owns scheduling per this repo's architecture) triggers it on its own schedule; no
in-backend scheduler exists.

#### Scenario: Running the creative loop returns evaluated survivors
- **WHEN** an admin or Hermes calls `POST /api/v1/sell-machine/creative-loop/run` with
  `{"count": 3}`
- **THEN** the response includes a `survivors` list of hooks that passed evaluation, generated with
  the telemetry report woven into the Copywriter's prompt

#### Scenario: An empty telemetry report does not block the loop
- **WHEN** `get_telemetry_report()` returns an empty/thin report (no completed operator tasks yet)
- **THEN** the endpoint still returns a non-empty `survivors` list (the same deterministic-fallback
  guarantee `generate_hooks` already provides)
