## MODIFIED Requirements

### Requirement: Autonomous Maintenance Cycle Scheduled (gbrain dream / autopilot)
The system SHALL enable and schedule GBrain's maintenance cycle (`gbrain dream`, composing lint → backlinks → sync → extract → embed → orphans) via `gbrain autopilot --install` or an equivalent cron entry, so the brain enriches itself autonomously: scanning recent captures for new entities, detecting and fixing missing cross-references/broken citations, consolidating scattered notes into compiled pages, and enriching existing entries. This runs on a recurring schedule without manual invocation. This capability — not manual curation — is the intended enrichment path once GBrain is live. (Referred to as "Dream Cycle" in Contexia's own docs/marketing framing; the underlying CLI command is `gbrain dream`.) The scheduling mechanism (`gbrain-autopilot.service`, a systemd user unit) SHALL be configured with `Restart=always`, so that GBrain's internal circuit-breaker exit (a clean, zero-status exit after repeated internal worker crashes, e.g. from a transient DB reconnect failure) still triggers an automatic restart — `Restart=on-failure` alone does not cover this exit mode.

#### Scenario: Maintenance cycle runs on schedule
- **WHEN** the configured schedule fires (e.g., nightly)
- **THEN** `gbrain dream` processes recent `contexia-brain/raw/` captures and updates compiled pages without a human triggering it

#### Scenario: New entity captured overnight becomes searchable
- **WHEN** a raw note mentioning a new entity is added, and the maintenance cycle subsequently runs
- **THEN** that entity is detected, linked, and returned by a hybrid-search query the next day

#### Scenario: Maintenance cycle failure is non-destructive
- **WHEN** a `gbrain dream` run fails or is interrupted
- **THEN** no source markdown is lost or corrupted (git remains the system of record) and the next run resumes safely, per `CycleReport`'s resumable phase design

#### Scenario: Service recovers automatically from an internal crash-loop exit
- **WHEN** the GBrain worker process crashes repeatedly (e.g. due to a transient DB reconnect failure) and GBrain's own internal circuit breaker gives up, exiting with status 0
- **THEN** systemd's `Restart=always` policy restarts `gbrain-autopilot.service` without requiring a human to run `systemctl restart` manually

## ADDED Requirements

### Requirement: GBrain Clone Upstream-Drift Is Documented and Reproducible
Local modifications to GBrain-clone files that are also tracked upstream (`skills/manifest.json`, `skills/RESOLVER.md`, needed so the generated Contexia agent skills are counted and discoverable) SHALL be re-appliable via a documented, single-command procedure after a `git pull` in the GBrain clone, so the drift is a known, recoverable trade-off rather than a silent risk of being overwritten.

#### Scenario: Re-applying the projection after an upstream pull
- **WHEN** `git pull` is run inside the GBrain clone and it updates `skills/manifest.json` or `skills/RESOLVER.md`
- **THEN** running `python scripts/generate_gbrain_skills.py` (documented in `docs/gbrain-adoption.md`) regenerates the Contexia skill projection and re-applies the manifest/resolver entries without manual reconstruction
