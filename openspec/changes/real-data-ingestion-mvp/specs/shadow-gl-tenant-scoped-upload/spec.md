### Requirement: Shadow GL ingestion endpoints resolve the tenant from the caller's JWT

All POST endpoints under `/api/v1/shadow-gl/*` SHALL require authentication
(`Depends(get_current_user)`) and SHALL resolve the target tenant through the canonical
resolver `core/tenant_context.py::resolve_request_tenant_scope()`.

They SHALL NOT resolve the tenant by querying `is_cliente_cero = true`. Before this change, a
client uploading their own accounting file had it written into Cliente Cero's ledger — a
data-segregation defect, and the endpoints were reachable unauthenticated.

#### Scenario: Unauthenticated upload is rejected
- **WHEN** a POST to `/api/v1/shadow-gl/upload` carries no `Authorization` header and
  `AUTH_ENFORCED` is on
- **THEN** the request is rejected with 401 and nothing is written

#### Scenario: A B2B client's upload lands in their own tenant
- **WHEN** an authenticated B2B client whose `resolved_tenant_id` is their own tenant uploads a file
- **THEN** the resulting journal entries carry that tenant's `tenant_id`, never Cliente Cero's

#### Scenario: A Contexia operator uploads on behalf of Cliente Cero
- **WHEN** the caller's resolved scope is Cliente Cero (operator)
- **THEN** the upload is ingested under Cliente Cero's tenant

#### Scenario: An authenticated caller with no resolvable tenant is refused
- **WHEN** an authenticated caller's tenant cannot be resolved
- **THEN** the request fails with 403 and does NOT fall back to Cliente Cero

#### Scenario: The hardcoded resolver is gone
- **WHEN** the source of the tenant resolver in `shadow_gl_endpoints.py` is inspected
- **THEN** it contains no `is_cliente_cero` query

---

### Requirement: A single upload endpoint accepts every supported format

`POST /api/v1/shadow-gl/upload` SHALL accept a multipart file of any format supported by
`parse_any_to_siigo_rows()` and SHALL record the attempt in `ingestion_batches` regardless of
outcome. It SHALL accept an `is_verified_real` flag defaulting to `false`, so nothing is
silently marked as genuine client data.

#### Scenario: A batch record is written even when parsing fails
- **WHEN** an upload fails to parse
- **THEN** the `ingestion_batches` row for that upload is updated to status `error` with the
  reason, and the client receives HTTP 400

#### Scenario: Unsupported format returns a client error, not a server error
- **WHEN** an upload carries an unsupported extension
- **THEN** the response is HTTP 400 naming the unsupported format, not a 500

#### Scenario: Re-uploading the same file does not duplicate entries
- **WHEN** the same file is uploaded twice for the same tenant
- **THEN** `ingest_siigo_csv()`'s idempotency on `(tenant_id, external_reference_id, entry_date)`
  prevents duplicate journal entries

---

### Requirement: The PWA offers self-service upload on Pulso

`contexia-app/components/pulso/DataUploadCard.tsx` SHALL let an authenticated client upload a
file from `/app/overview` using `authenticatedFetch`, and SHALL surface explicit
`idle`/`uploading`/`success`/`error` states.

It SHALL send `is_verified_real=true`, because a file a client uploads through their own
authenticated session is genuine client data.

The card SHALL only advertise formats the backend can actually parse.

#### Scenario: Successful upload reports what was ingested
- **WHEN** an upload succeeds
- **THEN** the card shows the imported row count and the date range returned by the backend

#### Scenario: A failed upload shows the backend's reason
- **WHEN** the backend returns an error
- **THEN** the card shows that reason and offers a retry, and never presents mock data as if it
  were real
