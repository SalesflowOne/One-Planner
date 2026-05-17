# Deploy Plane on Coolify

This repository includes `docker-compose.coolify.yml` for deploying the full Plane Community stack on Coolify:

- Caddy proxy
- Web, Admin, Space, and Live apps
- Django API
- Celery worker and beat worker
- PostgreSQL, Redis, RabbitMQ, and MinIO

## Coolify setup

1. In Coolify, create a new **Docker Compose** resource from this repository.
2. Set the compose file path to:

   ```text
   docker-compose.coolify.yml
   ```

3. Assign your public domain to the `proxy` service on port `80`.
4. Copy the variables from `.env.coolify.example` into the Coolify environment.
5. Set `PLANE_PUBLIC_URL` to the exact public URL Coolify will serve, without a trailing slash.
6. Generate unique values for every secret in `.env.coolify.example`.
7. Deploy.

After the first successful deploy, visit:

```text
https://your-plane-domain.example/god-mode/
```

Create the first instance administrator, then use the same credentials to sign in to the main app.

## Notes

- TLS should be handled by Coolify's reverse proxy. The internal Plane `proxy` service listens on HTTP port `80`.
- The frontend apps are built to use same-origin API paths, so the public app, `/api`, `/auth`, `/god-mode`, `/spaces`, `/live`, and file uploads all route through the Caddy proxy.
- The default compose uses internal MinIO storage. To use external S3-compatible storage, update the storage variables and remove or ignore the `plane-minio` service.
- Keep `ENABLE_EMAIL_PASSWORD=1` for the initial setup unless another authentication provider is configured.
