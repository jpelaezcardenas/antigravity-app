# Backend local environment

## Why a venv is mandatory here

This machine's **global** Python 3.11 install is shared with Hermes and the local pollers.
`hermes-agent` pins `pydantic==2.13.4` **exactly**, while this backend pins `pydantic==2.5.0`
(with `fastapi==0.104.1`) in `requirements.txt` — the versions Railway installs.

Those two are mutually incompatible in one interpreter: FastAPI 0.104.1 running against
pydantic 2.13.x raises `AttributeError: 'FieldInfo' object has no attribute 'in_'` at import
time. Do **not** "fix" that by downgrading the global pydantic — that breaks Hermes, which per
`ARCHITECTURE.md` decision #1 is the local orchestrator.

Use a venv instead. It is already covered by `.gitignore`.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Run tests

```bash
.venv/Scripts/python.exe -m pytest tests/ -q
```

## Why this matters beyond convenience

Running tests against the global environment gives **different behavior than production**.
The version drift masked a real regression: `main.py` referenced `APIRouter` without importing
it, and because that block is wrapped in `try/except`, the internal routers silently failed to
register — the app still booted, just without `/internal/siigo-sync/run` and
`/internal/ingest/file`. It surfaced only once tests ran against the pinned versions.

Rule of thumb: if a `try/except` around router registration logs an error, treat it as a
failure, not a warning.
