# Fix — GET / health check test coverage (chatwoot-hermes-taty-bridge, task5-10)

## Scope

Single blocking finding from `progress/review_chatwoot-hermes-taty-bridge-task5-10.md`:
`GET /` (main.py:108-112) had zero test coverage. No other file was touched.

## What was added

New file: `apps/chatwoot-bridge/tests/test_health.py`

- `TestHealthCheck::test_health_check_succeeds_and_invokes_hermes_liveness_check`
  - Uses the same in-process `httpx.ASGITransport(app=main_module.app)` pattern already
    used in `tests/test_webhook_filter.py`.
  - `GET /` -> asserts HTTP 200.
  - Asserts JSON body: `service == "chatwoot-hermes-bridge"`, `status == "ok"`, and
    `hermes_models` equals the mocked payload returned by `hermes_client.check_models()`
    (matching main.py's actual response shape, read directly before writing the test —
    no shape was guessed).
  - Patches `main_module.hermes_client.check_models` with an `AsyncMock` (confirmed
    `check_models` is `async def` in `hermes_client.py:58`) and asserts
    `mock_check_models.assert_awaited_once_with()` — proving the endpoint genuinely
    invokes the Hermes liveness check during the request, not just that the response
    shape happens to match.

## Verification

```
cd apps/chatwoot-bridge && python -m pytest tests -v
```

Result: **32 passed, 1 warning** (the 1 warning is the pre-existing, unrelated
`python_multipart` `PendingDeprecationWarning` noted in the prior review — nothing new).

All 31 prior tests remain green; the new `test_health.py::TestHealthCheck::test_health_check_succeeds_and_invokes_hermes_liveness_check`
test passes.

## Files touched

- `apps/chatwoot-bridge/tests/test_health.py` (new file, added only)

No other file was modified — `main.py`, `hermes_client.py`, and `tasks.md` are untouched.
