# Deployment Guide

## Architecture Overview

This project uses a split-stack deployment:
- **Frontend**: Vercel (Next.js)
- **Backend**: VPS (Dockerized FastAPI behind host-level Caddy)

## Environment Configuration

### Frontend Environment Variables

Set these in Vercel Dashboard → Project Settings → Environment Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | `eyJhbG...` |
| `NEXT_PUBLIC_BACKEND_URL` | VPS backend URL (prod) | `https://api.example.com` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL (prod) | `wss://api.example.com/ws` |
| `NEXT_PUBLIC_LIVE_TRANSPORT` | Transport type | `websocket` |
| `NEXT_PUBLIC_GEMINI_API_KEY` | Gemini API key | `AIza...` |
| `NEXT_PUBLIC_MODEL` | Gemini model | `gemini-3.1-flash-live-preview` |

### GitHub Secrets

Configure these in GitHub → Repository Settings → Secrets and variables → Actions:

#### Vercel (Required for frontend deployment)
- `VERCEL_TOKEN` - Vercel personal access token
- `VERCEL_ORG_ID` - Vercel organization ID (from `.vercel/project.json`)
- `VERCEL_PROJECT_ID` - Vercel project ID (from `.vercel/project.json`)

#### Preview VPS (Optional - for preview backend)
- `PREVIEW_VPS_HOST` - Preview server hostname (e.g., `preview-api.example.com`)
- `PREVIEW_VPS_USER` - SSH user for preview server
- `PREVIEW_VPS_SSH_KEY` - SSH private key for preview server
- `PREVIEW_VPS_DEPLOY_PATH` - Deployment path on preview server
- `PREVIEW_VPS_SERVICE` - Existing preview systemd service name

#### Production VPS (Required for production backend)
- `PROD_VPS_HOST` - Production server hostname (e.g., `api.example.com`)
- `PROD_VPS_USER` - SSH user for production server
- `PROD_VPS_SSH_KEY` - SSH private key for production server
- `PROD_VPS_DEPLOY_PATH` - Deployment path on production server
- `PROD_VPS_CONTAINER_NAME` - Stable Docker container name (e.g., `interview-backend`)
- `PROD_VPS_ENV_FILE` - Absolute path to the backend env file on the VPS
- `PROD_VPS_HOST_PORT` - Loopback-only host port Caddy will proxy to (e.g., `8000`)

## CI/CD Pipeline

### Job Structure

The workflow now includes a backend container build smoke check before deploy:

1. `lint_backend` - Backend linting with ruff
2. `test_backend` - Backend tests with pytest
3. `lint_frontend` - Frontend linting with ESLint
4. `build_frontend` - Frontend production build
5. `smoke_backend_startup` - Verify FastAPI starts in a Python env
6. `smoke_backend_container_build` - Verify the backend Docker image builds
7. `deploy_preview_backend` - Deploy preview backend to VPS (PR only)
8. `deploy_vercel_preview` - Deploy frontend preview to Vercel
9. `deploy_prod_backend` - Build and restart the production Docker container on VPS
10. `deploy_vercel_production` - Deploy frontend production to Vercel
11. `post_deploy_smoke_*` - Smoke tests after deployment

### Deployment Triggers

| Event | Backend Deploy | Frontend Deploy |
|-------|----------------|-----------------|
| PR opened/updated | Preview VPS | Vercel Preview |
| Push to `main` | Production VPS | Vercel Production |

## VPS Backend Setup

### Required Software
- Docker Engine
- Caddy
- Git
- curl

### Build And Run The Backend Container

```bash
cd /srv/ai-interview-backend
git pull origin main
mkdir -p uploads
docker build -t interview-backend:latest .
docker rm -f interview-backend 2>/dev/null || true
docker run -d \
  --name interview-backend \
  --restart unless-stopped \
  --env-file /etc/ai-interview/backend.env \
  -p 127.0.0.1:8000:8000 \
  -v /srv/ai-interview-backend/uploads:/app/uploads \
  interview-backend:latest
```

The `uploads/` bind mount keeps uploaded files across container replacements.

### Backend Environment File

Create an env file on the VPS, for example `/etc/ai-interview/backend.env`:

```env
GEMINI_API_KEY=your-gemini-api-key
JWT_SECRET_KEY=replace-me
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-supabase-jwt-secret
SUPABASE_DB_URL=postgresql://...
DIRECT_URL=postgresql://...
MODEL_LIVE=gemini-3.1-flash-live-preview
MODEL_EXTRACT=gemini-2.5-flash
ENV=production
CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app
```

`CORS_ALLOWED_ORIGINS` is the production source of truth for browser access.

### Caddy Configuration

Point your API hostname DNS record to the VPS, then configure Caddy on the host to proxy to the loopback-only Docker port:

```caddyfile
api.example.com {
    reverse_proxy 127.0.0.1:8000
}
```

Caddy handles TLS automatically. WebSocket upgrades for `/ws` are proxied through the same upstream.

### Validation

```bash
curl http://127.0.0.1:8000/health
curl https://api.example.com/health
curl -i \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  https://api.example.com/ws
```

Expected result:
- `/health` returns HTTP 200
- `/ws` returns a WebSocket handshake-related status such as `101`, `400`, `403`, `404`, or `426`

### Production Deploy Workflow

The GitHub Actions production job now deploys by:

```bash
git fetch origin main
git checkout main
git reset --hard <target_sha>
mkdir -p uploads
docker build -t <container>:<sha> -t <container>:latest .
docker rm -f <container> || true
docker run -d \
  --name <container> \
  --restart unless-stopped \
  --env-file <env_file> \
  -p 127.0.0.1:<host_port>:8000 \
  -v <deploy_path>/uploads:/app/uploads \
  <container>:latest
curl http://127.0.0.1:<host_port>/health
```

Preview backend deployment is still host-managed and can be containerized later if needed.
