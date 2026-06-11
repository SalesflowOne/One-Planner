# OnePlan.one — Implementation Guide

OnePlan extends Plane with AI operator, Flow & Constraints, Supabase auth adapter, and MCP integration.

## Feature Flags

Set in `apps/api/.env` or God Mode instance configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ONEPLAN_FEATURES` | `1` | Master switch |
| `ENABLE_AI_OPERATOR` | `1` | Alfred AI operator |
| `ENABLE_FLOW_CONSTRAINTS` | `1` | Objectives & constraints |
| `ENABLE_SUPABASE_AUTH` | `0` | Supabase JWT → Django session |
| `ENABLE_CEO_COMMAND_MODE` | `1` | Command Center dashboard |
| `AI_ACTION_REQUIRE_APPROVAL` | `1` | Require approval for write actions |

## API Endpoints

### Internal (session auth) — `/api/oneplan/`

- `GET /api/oneplan/config/` — feature flags
- `POST /api/oneplan/workspaces/:slug/chat/` — AI chat (modes: ask, plan, act)
- `POST /api/oneplan/workspaces/:slug/actions/approve/` — approve previewed action
- `GET /api/oneplan/workspaces/:slug/constraints/` — list constraints
- `GET /api/oneplan/workspaces/:slug/command/` — command center data

### External (API key) — `/api/v1/`

- `GET /api/v1/workspaces/:slug/summary/`
- `GET /api/v1/workspaces/:slug/constraints/`
- `POST /api/v1/workspaces/:slug/tools/execute/`

### Auth

- `POST /auth/supabase/` — exchange Supabase JWT for Django session

## MCP Server

```bash
cd packages/oneplan-mcp
pnpm install && pnpm build
ONEPLAN_API_URL=http://localhost:8000 \
ONEPLAN_API_KEY=plane_api_... \
ONEPLAN_WORKSPACE_SLUG=my-workspace \
pnpm start
```

## Database Migration

```bash
docker compose run migrator
# or locally: python manage.py migrate oneplan
```

## Frontend Routes

- `/:workspaceSlug/oneplan/command` — Command Center
- `/:workspaceSlug/oneplan/focus` — Constraints dashboard
- `/:workspaceSlug/oneplan/assistant` — Alfred AI operator

## Coolify / Docker

No new containers required. Add OnePlan env vars to `plane.env` and rebuild frontends with:

```
VITE_APP_NAME=OnePlan
VITE_WEBSITE_URL=https://oneplan.one
```

Backup before migration:

```bash
./setup.sh  # option 7 — backup volumes
```
