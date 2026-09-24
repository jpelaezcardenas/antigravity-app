## ADDED Requirements

### Requirement: A scheduled job sends the founder a daily GTM/ops digest via Telegram
The system SHALL run a scheduled job, at most once per day, that assembles a digest covering ad
spend/lead attribution, new lead count, Approval Queue backlog count, and Manus (`operator_tasks`)
task status, and sends it via the existing `send_telegram_message(chat_id, text)` to the founder's
configured `chat_id`.

#### Scenario: Daily digest is sent at the scheduled time
- **WHEN** the scheduled digest job runs
- **THEN** it sends exactly one Telegram message to the founder's `chat_id` containing all four
  data sections

#### Scenario: Digest never fires more than once per day
- **WHEN** the job is triggered more than once within the same calendar day (e.g. manual re-run
  plus the schedule)
- **THEN** only one digest message is sent per day, per data section semantics defined by the
  implementation (no duplicate daily summaries)

### Requirement: A digest field with no real data source reports an explicit missing-data state
Any digest section that cannot be computed from a real query (e.g. no CAPI/ad-spend data configured
yet, zero `operator_tasks` rows) SHALL render an explicit "no disponible" / "sin datos suficientes"
label for that section. The system SHALL NEVER estimate, interpolate, or omit-without-explanation a
value it cannot compute from real data.

#### Scenario: Ad spend data is not yet available
- **WHEN** the digest job runs and no ad-spend/attribution data source is configured or returns
  data
- **THEN** the digest's ad-spend section explicitly states it is unavailable, rather than showing
  zero or a guessed figure

#### Scenario: Approval Queue and lead-count sections always reflect real counts
- **WHEN** the digest job runs
- **THEN** the Approval Queue backlog count and new-lead count sections are computed directly from
  `approval_queue` and `crm_leads`/`b2b_clients` respectively, never hardcoded or cached beyond the
  current run

### Requirement: The digest job never blocks or degrades other scheduled jobs
The digest job SHALL be independent of other Hermes Scheduled Jobs (Pulso Diario, Centinela Fiscal,
etc.) — its failure SHALL NOT prevent other jobs from running, and its data sources SHALL be
read-only queries against existing tables.

#### Scenario: Digest job failure does not affect other scheduled jobs
- **WHEN** the digest job raises an unhandled error (e.g. Telegram API unavailable)
- **THEN** the error is logged and the job exits; no other Hermes Scheduled Job's execution is
  affected
