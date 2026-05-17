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

Plane is a monorepo with two runtime stacks:

- **Frontend/Node** (pnpm + Turborepo): `apps/web` (:3000), `apps/admin` (:3001), `apps/space` (:3002), `apps/live` (:3100), plus shared packages in `packages/`
- **Backend/Python** (Django): `apps/api` (:8000) runs inside Docker alongside PostgreSQL, Valkey/Redis, RabbitMQ, and MinIO

### Starting the development environment

1. **Backend services** (Docker required): `docker compose -f docker-compose-local.yml up -d`
   - Starts: PostgreSQL 15, Valkey 7.2, RabbitMQ 3.13, MinIO, Django API, Celery worker/beat, migrator
   - Wait for the `migrator` container to exit before testing the API
2. **Frontend dev servers**: `pnpm dev` (starts web, admin, space, and live via Turborepo)

### Non-obvious gotchas

- **Docker daemon**: requires `fuse-overlayfs` storage driver and `iptables-legacy` in this cloud VM. Docker socket may need `sudo chmod 666 /var/run/docker.sock` after starting `dockerd`.
- **API .env MinIO setting**: the `apps/api/.env` must have `AWS_S3_ENDPOINT_URL="http://plane-minio:9000"` (Docker network name) and `USE_MINIO=1` for the API container to reach MinIO. The `.env.example` defaults to `localhost:9000` which won't work inside Docker.
- **Cover image uploads in dev**: without the Caddy proxy, project cover image uploads fail because presigned URLs are generated with `request.get_host()` (pointing to the API host, not MinIO). This is a cosmetic issue; core functionality works fine.
- **Node version**: requires `>=22.18.0`. The VM has nvm with a suitable version pre-installed.
- **Package manager**: pnpm 10.32.1 via corepack (`corepack enable pnpm`).
- **Pre-commit hook**: runs `pnpm lint-staged` (oxfmt + oxlint with `--fix --deny-warnings`).
- **`pnpm check:lint`** reports ~1000 warnings but 0 errors — this is normal for the codebase.
- **Admin registration**: first user registered at `http://localhost:3001/god-mode/` becomes the instance admin. The same credentials work at `http://localhost:3000/`.
