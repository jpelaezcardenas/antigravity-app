## ADDED Requirements

### Requirement: Unmatched fiscal questions are answered via KB-grounded reasoning
The system SHALL, when `classify_lead_intent` returns `unknown`, use one anonymized LLM call
(`agents.secure_llm.get_anonymized_ai_response`) to determine whether the message is a fiscal
question and, if so, a search query for it. If it is a fiscal question, the system SHALL call
`services.kb_seeding_service.retrieve_similar` against the shared `"__global__"` KB pool and use a
second anonymized LLM call to synthesize a reply grounded in the retrieved chunks. If no chunks are
retrieved, or the message is not a fiscal question, or either LLM call fails, the system SHALL fall
back to the pre-existing static reply rather than crashing or hallucinating an ungrounded answer.

#### Scenario: A fiscal question with matching KB content gets a grounded reply
- **WHEN** an unmatched message is classified as a fiscal question and `retrieve_similar` returns
  one or more chunks
- **THEN** Taty's reply is synthesized from those chunks via the second LLM call, not the static
  fallback reply

#### Scenario: A fiscal question with no matching KB content gets a graceful fallback
- **WHEN** an unmatched message is classified as a fiscal question but `retrieve_similar` returns
  zero chunks
- **THEN** Taty's reply states she doesn't have that information and an advisor can help, without
  calling the second (synthesis) LLM call

#### Scenario: A non-fiscal unmatched message keeps the original static reply
- **WHEN** an unmatched message is classified as not a fiscal question
- **THEN** Taty's reply is the pre-existing static "No estoy segura de tu pregunta..." message,
  unchanged from before this requirement existed

#### Scenario: An LLM failure at either call site degrades gracefully
- **WHEN** `get_anonymized_ai_response` raises an exception at the classification or synthesis step
- **THEN** Taty's reply falls back to the pre-existing static message rather than the request
  failing
