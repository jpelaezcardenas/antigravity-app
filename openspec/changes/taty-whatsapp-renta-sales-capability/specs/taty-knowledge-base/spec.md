## ADDED Requirements

### Requirement: knowledge_chunks schema matches its own retrieval code
The `knowledge_chunks` table SHALL have a `client_id` column, and the database SHALL expose a
`match_knowledge_chunks(query_embedding vector, p_client_id text, match_count int)` RPC overload,
matching the signature `services/kb_seeding_service.py::retrieve_similar` already calls. This
addition SHALL be additive — the pre-existing `match_knowledge_chunks(query_embedding,
match_threshold, match_count)` overload and any other existing consumer SHALL continue to work
unmodified.

#### Scenario: Seeding succeeds against the live schema
- **WHEN** `kb_seeding_service.seed_chunks` is called against the live `knowledge_chunks` table
- **THEN** the insert succeeds and includes a `client_id` value, with no schema error

#### Scenario: retrieve_similar's actual call signature succeeds
- **WHEN** `retrieve_similar(query, client_id, top_k)` calls `match_knowledge_chunks` with
  `(query_embedding, p_client_id, match_count)`
- **THEN** the RPC executes and returns matching rows scoped to that `client_id`, with no
  "function does not exist" error

#### Scenario: The pre-existing match_threshold overload is unaffected
- **WHEN** an existing caller invokes `match_knowledge_chunks(query_embedding, match_threshold,
  match_count)`
- **THEN** it continues to resolve and behave exactly as before this change

### Requirement: Renta-persona-natural content is seeded with only confirmed figures
The knowledge base SHALL include a seed set of chunks covering the declaración de renta persona
natural offer (current thresholds, filing deadlines by cédula digit, required documents, price,
what Contexia as Entidad B can and cannot do). Every fiscal figure in the seed set SHALL be traced
to a confirmed source; no chunk SHALL contain an invented or unconfirmed number.

#### Scenario: Seeded content is retrievable for a real question
- **WHEN** a lead asks a renta-persona-natural question covered by the seed set (e.g. filing
  deadline for their cédula's last digit)
- **THEN** `retrieve_similar` returns the relevant chunk(s) with a non-empty result

#### Scenario: No unconfirmed figure enters the seed set
- **WHEN** the seed content is reviewed before loading
- **THEN** every fiscal number present traces to a confirmed source (current DIAN calendar,
  Contexia's actual pricing) — content with an unconfirmed figure is excluded, not approximated
