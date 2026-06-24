## ADDED Requirements

### Requirement: Maestro fans out status checks to all registered agents in parallel
The system SHALL maintain a registry of agents exposing an async `quick_status()` call, and SHALL invoke all of them concurrently via `asyncio.gather` when a swarm status is requested.

#### Scenario: All agents healthy
- **WHEN** a client calls `POST /api/v1/hermes/swarm/invoke` with `{action: "status"}`
- **THEN** Maestro calls `quick_status()` on every registered agent concurrently
- **AND** the response includes a per-agent status entry for all of them

#### Scenario: Only async agents can be registered
- **WHEN** an agent is registered whose `quick_status` is not an `async def`
- **THEN** registration SHALL fail at startup (CI/type check), preventing it from blocking the fan-out at runtime

### Requirement: Swarm status fan-out completes within budget even with partial failure
The system SHALL enforce a per-agent timeout so that one slow or failing agent does not block the overall response beyond the stated budget, and SHALL report partial failures rather than failing the whole request.

#### Scenario: One agent times out
- **WHEN** one agent's `quick_status()` does not return within its per-agent timeout
- **THEN** that agent's entry is marked `status: "timeout"` in the response
- **AND** the responses from all other agents are still included

#### Scenario: Overall response stays within the latency budget
- **WHEN** all agents are registered with a per-agent timeout no greater than the overall budget
- **THEN** `POST /api/v1/hermes/swarm/invoke {action: "status"}` SHALL return within 500ms p95 under normal conditions

#### Scenario: One agent raises an exception
- **WHEN** one agent's `quick_status()` raises an unhandled exception
- **THEN** the exception is caught per-agent
- **AND** that agent's entry is marked `status: "error"` with the exception message, without crashing the overall request
