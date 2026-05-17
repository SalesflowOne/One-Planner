# Agent Development Guide

## Commands

- `pnpm dev` - Start all dev servers (web:3000, admin:3001)
- `pnpm build` - Build all packages and apps
- `pnpm check` - Run all checks (format, lint, types)
- `pnpm check:lint` - OxLint across all packages
- `pnpm check:types` - TypeScript type checking
- `pnpm fix` - Auto-fix format and lint issues
- `pnpm turbo run <command> --filter=<package>` - Target specific package/app
- `pnpm --filter=@plane/ui storybook` - Start Storybook on port 6006

## Code Style

- **Imports**: Use `workspace:*` for internal packages, `catalog:` for external deps
- **TypeScript**: Strict mode enabled, all files must be typed
- **Formatting**: oxfmt, run `pnpm fix:format`
- **Linting**: OxLint with shared `.oxlintrc.json` config
- **Naming**: camelCase for variables/functions, PascalCase for components/types
- **Error Handling**: Use try-catch with proper error types, log errors appropriately
- **State Management**: MobX stores in `packages/shared-state`, reactive patterns
- **Testing**: All features require unit tests, use existing test framework per package
- **Components**: Build in `@plane/ui` with Storybook for isolated development

## Cursor Cloud specific instructions

### Architecture overview

Plane is a monorepo with a Python/Django backend (in `apps/api/`, runs via Docker) and TypeScript/React frontends (`apps/web`, `apps/admin`, `apps/space`, `apps/live`). Infrastructure services (PostgreSQL, Valkey/Redis, RabbitMQ, MinIO) also run via Docker.

### Starting the dev environment

1. **Docker must be running** before starting services. Start dockerd if not already running: `sudo dockerd &>/tmp/dockerd.log &` then `sudo chmod 666 /var/run/docker.sock`.
2. **Backend + infrastructure**: `docker compose -f docker-compose-local.yml up -d` (starts Postgres, Redis, RabbitMQ, MinIO, Django API on :8000, Celery worker, Celery beat, and runs migrations).
3. **Frontend dev servers**: `pnpm dev` (starts web:3000, admin:3001, space:3002, live:3100).
4. **First-time setup**: Register as instance admin at http://localhost:3001/god-mode/, then log into the main app at http://localhost:3000/.

### Gotchas

- The API `.env` must have `USE_MINIO=1` and `AWS_S3_ENDPOINT_URL="http://plane-minio:9000"` (Docker network hostname) for file uploads to work since the API container communicates with MinIO over the Docker bridge network.
- The migrator container runs once and exits with code 0 when done. Wait for it to complete before testing the API.
- `pnpm check:lint` produces ~1000 warnings but 0 errors — this is expected.
- The pre-commit hook runs `pnpm lint-staged` (oxfmt + oxlint with `--fix`).
- Node.js >= 22.18.0 is required (set in `.mise.toml` and `package.json` engines).
