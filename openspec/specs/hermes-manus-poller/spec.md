## ADDED Requirements

### Requirement: A local poller consumes the operator-task queue
The system SHALL provide a local-only service that periodically polls
`GET /api/v1/sell-machine/tasks/pending`, dispatches each task to the Manus API, and reports the
terminal result back via `POST /api/v1/sell-machine/tasks/{id}/result`. It SHALL run on the
founder's local node only, never on Railway or Vercel.

#### Scenario: A pending task reaches Manus
- **WHEN** an approved `post_content` task is `pending` and the poller runs
- **THEN** the task is marked `dispatched` and a Manus task is created with the task's payload

#### Scenario: A finished Manus task is reported back
- **WHEN** a dispatched task's Manus status becomes `stopped`
- **THEN** the operator task is reported as `completed`, carrying `task_url` and `credit_usage`

#### Scenario: A failed Manus task is reported back
- **WHEN** a dispatched task's Manus status becomes `error`
- **THEN** the operator task is reported as `failed`

### Requirement: The poller fails closed without credentials
The system SHALL check for a configured Manus API key BEFORE claiming any task, and SHALL exit
without side effects when it is absent.

#### Scenario: Unconfigured node claims nothing
- **WHEN** `MANUS_API_KEY` is empty and the poller runs
- **THEN** no task is claimed, no HTTP call is made to Manus, and the run reports itself as skipped

### Requirement: The poller never double-dispatches a task
The system SHALL claim a task (`pending -> dispatched`) before creating its Manus task, and SHALL
NOT create a Manus task when the claim is rejected. A task that was claimed but whose Manus task
could not be created SHALL be surfaced as an orphan rather than automatically retried.

#### Scenario: A rejected claim stops the dispatch
- **WHEN** the backend rejects `mark_dispatched` (e.g. another tick already claimed it)
- **THEN** no Manus task is created for that operator task

#### Scenario: An orphan is reported, not retried
- **WHEN** a task was claimed but `task.create` failed
- **THEN** it is logged as an orphan and left for manual resolution, never re-dispatched automatically

### Requirement: Approved copy is published unchanged
For side-effecting task types (`post_content`, `run_ads_ab`), the prompt sent to Manus SHALL state
that the content was already approved by a human and must be published as written, without
rewriting figures, prices or contact data.

#### Scenario: Side-effecting prompt carries the approval banner
- **WHEN** a `post_content` or `run_ads_ab` task is dispatched
- **THEN** its Manus prompt instructs the agent not to rewrite or "improve" the approved content

#### Scenario: An unknown task type performs no external action
- **WHEN** a task has a `task_type` the poller does not recognize
- **THEN** the prompt explicitly forbids any externally-visible action and asks Manus to stop and report
