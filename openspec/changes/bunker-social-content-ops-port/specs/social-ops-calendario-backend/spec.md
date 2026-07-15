## ADDED Requirements

### Requirement: Calendario endpoint reads from the canonical Supabase project
`GET /api/v1/social-ops/calendario` SHALL return editorial calendar entries, preferring the canonical Supabase project's `calendario` table when `SUPABASE_URL`/`SUPABASE_KEY` are configured and the query succeeds, and falling back to in-memory demo data otherwise — never raising a hard error to the caller.

#### Scenario: Supabase configured and table exists
- **WHEN** `GET /social-ops/calendario` is called with Supabase env vars set and the `calendario` table reachable
- **THEN** the response has `"source": "supabase"` and `items` populated from the real table

#### Scenario: Supabase unavailable or table missing
- **WHEN** `GET /social-ops/calendario` is called and the Supabase query raises any exception
- **THEN** the response has `"source": "demo_fallback"` and `items` populated from in-memory seed data — the endpoint still returns HTTP 200

### Requirement: Calendario endpoint supports week filtering
`GET /api/v1/social-ops/calendario` SHALL accept an optional `semana` query parameter and, when provided, SHALL return only entries matching that week.

#### Scenario: Filtering by week
- **WHEN** `GET /social-ops/calendario?semana=2` is called
- **THEN** every item in the response has `semana == 2`
