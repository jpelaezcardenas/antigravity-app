### Requirement: Borradores list endpoint reads from the canonical Supabase project
`GET /api/v1/social-ops/borradores` SHALL return content drafts with status `BORRADOR_IA` or `EDITADO_HUMANO`, preferring the canonical Supabase project's `contenido` table when configured and reachable, and falling back to in-memory demo data otherwise.

#### Scenario: Only pending-review drafts are returned
- **WHEN** `GET /social-ops/borradores` is called
- **THEN** every item in `items` has `status` equal to `BORRADOR_IA` or `EDITADO_HUMANO` — approved or published drafts are excluded

### Requirement: Borradores approve endpoint
`POST /api/v1/social-ops/borradores/{id}/approve` SHALL set the draft's status to `APROBADO`, record `fecha_aprobacion` as today's date, and record `aprobado_por` from the request actor.

#### Scenario: Approving a draft
- **WHEN** `POST /social-ops/borradores/42/approve` is called with a valid draft id
- **THEN** the draft's status becomes `APROBADO` and it no longer appears in `GET /social-ops/borradores`

#### Scenario: Approving a non-existent draft
- **WHEN** `POST /social-ops/borradores/{id}/approve` is called with an id that doesn't exist
- **THEN** the endpoint returns HTTP 404

### Requirement: Borradores update endpoint
`POST /api/v1/social-ops/borradores/{id}/update` SHALL apply a partial update to `hook`, `hook_alt_1`, `hook_alt_2`, `copy_body`, `cta`, and/or `hashtags`, and SHALL set `status` to `EDITADO_HUMANO` when the update includes content field changes.

#### Scenario: Editing a draft's hook and copy
- **WHEN** `POST /social-ops/borradores/42/update` is called with `{"hook": "...", "copy_body": "..."}`
- **THEN** the draft's `hook` and `copy_body` are updated and its `status` becomes `EDITADO_HUMANO`
