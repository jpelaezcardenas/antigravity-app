## MODIFIED Requirements

### Requirement: Copywriter generates a bounded batch of marketing hooks
The system SHALL expose `POST /api/v1/sell-machine/hooks/generate`, which SHALL generate N
marketing hooks (default N=5, `{headline, body, cta, pain_tag}` each) via the LLM engine, grounded
in DIAN-pains content retrieved via `services.kb_seeding_service.retrieve_similar` against the
shared `"__global__"` KB pool, and SHALL fall back to a deterministic hook set if all LLM providers
fail (never erroring the request). KB retrieval failure or an empty result SHALL NOT block
generation — hooks are still produced without the grounding section in that case.

#### Scenario: Generating hooks returns the requested count
- **WHEN** an admin calls `POST /api/v1/sell-machine/hooks/generate` with `{"count": 5}`
- **THEN** the response includes 5 hooks, each with `headline`, `body`, `cta`, and `pain_tag`

#### Scenario: LLM provider failure falls back to a deterministic hook set
- **WHEN** `POST /api/v1/sell-machine/hooks/generate` is called and all configured LLM providers
  fail
- **THEN** the response still returns a non-empty set of hooks (the deterministic fallback), and
  the request does not error

#### Scenario: Hook generation is grounded in retrieved KB content
- **WHEN** `retrieve_similar` returns one or more DIAN-pains chunks for the generation query
- **THEN** those chunks are included in the LLM prompt as grounding context before hooks are
  generated

#### Scenario: KB retrieval failure does not block hook generation
- **WHEN** `retrieve_similar` raises or returns zero chunks
- **THEN** hook generation proceeds without a grounding section, producing the same shape of
  result as before this requirement existed
