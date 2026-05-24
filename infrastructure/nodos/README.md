# Nodos Contexia — Local Node Infrastructure

**Status:** Draft (2026-05-27, PHASE 2 DAY 3 T13). Not yet deployed.

## What this is

A Docker Compose deployment for a local Contexia node, intended to run at
partner coworking spaces. Each node provides:

- **n8n** — workflow automation for client-specific routines.
- **NAS-mock (Minio)** — local document storage (real Synology/Truenas in
  production).
- **VPN tunnel (stub)** — secure path to the central Contexia API.

The node holds **no regulated data at rest**. All operations call the central
API with SOSP-compliant anonymized payloads.

## Quick start (after CLI init)

```bash
# 1. Generate per-node env from the CLI
python infrastructure/nodos/cli/contexia-node.py init \
    --company "Corp A" --location envigado

# 2. Move env to the compose directory
mv .env.node-envigado-corp-a infrastructure/nodos/.env.node

# 3. Bring the node up
cd infrastructure/nodos
docker compose --env-file .env.node up -d

# 4. Check
docker compose ps
curl http://localhost:5678   # n8n
curl http://localhost:9001   # Minio console
```

## What's in scope for MVP

- Docker Compose definitions for n8n + Minio.
- CLI `init` command that generates a safe `.env.node` with random secrets.
- README + example env documenting the layout.

## What's stubbed (future work)

- WireGuard VPN tunnel service (commented in compose).
- `contexia-node` CLI commands: `status`, `sync`, `teardown`.
- Auto-registration of the node in the central API.
- Wizard endpoint `/wizard/auditoria-sombra` integration (15-min free audit).

## Validation

```bash
# Parse compose file without running anything
docker compose -f infrastructure/nodos/docker-compose.yml config

# Lint CLI
python infrastructure/nodos/cli/contexia-node.py --help
python infrastructure/nodos/cli/contexia-node.py init --help
```

## Architecture

See `specs/phase2-nodos-contexia.md` for design rationale (to be written T14).
