# Deployment

## Environments

| Environment | Purpose | Infra |
|-------------|---------|-------|
| Local | Development | Docker Compose |
| Staging | Testing | Single VPS |
| Production | Users | VPS + managed DB (optional) |

## Local Development

### Prerequisites

```bash
# Required
docker >= 24.0
docker-compose >= 2.20
python >= 3.11
node >= 20 (for frontend)

# Optional
just  # command runner (cargo install just)
```

### Quick Start

```bash
git clone <repo>
cd socratic-learning

# Copy env
cp .env.example .env
# Edit .env: add OPENROUTER_API_KEY

# Start all services
docker-compose up -d

# API: http://localhost:8000
# Frontend: http://localhost:3000
# ChromaDB: http://localhost:8001
```

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://app:app@postgres:5432/socratic
      - CHROMADB_HOST=chromadb
      - CHROMADB_PORT=8000
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - chromadb
    command: uvicorn app.main:app --reload --host 0.0.0.0

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: socratic
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chromadb_data:/chroma/chroma
    ports:
      - "8001:8000"
    environment:
      - ANONYMIZED_TELEMETRY=False

volumes:
  postgres_data:
  chromadb_data:
```

## Production Deployment

### Option 1: Single VPS (Hetzner/DigitalOcean)

**Specs for 100 users**:
- 2 vCPU, 4GB RAM, 80GB SSD
- ~$12-20/month

```
┌─────────────────────────────────────────┐
│              VPS (Ubuntu 22.04)         │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Caddy   │  │ FastAPI │  │ChromaDB │  │
│  │ (proxy) │─▶│  :8000  │  │ :8001   │  │
│  └─────────┘  └─────────┘  └─────────┘  │
│       │                                 │
│       ▼                                 │
│  ┌─────────────────────────────────┐    │
│  │         PostgreSQL :5432        │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Volumes: /data/postgres, /data/chroma  │
└─────────────────────────────────────────┘
```

### Docker Compose (Production)

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  api:
    image: ghcr.io/${GITHUB_REPO}/api:${VERSION:-latest}
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CHROMADB_HOST=chromadb
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - chromadb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: ghcr.io/${GITHUB_REPO}/frontend:${VERSION:-latest}
    restart: always

  caddy:
    image: caddy:2-alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config

  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: socratic
    volumes:
      - postgres_data:/var/lib/postgresql/data

  chromadb:
    image: chromadb/chroma:latest
    restart: always
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - CHROMA_SERVER_AUTH_CREDENTIALS=${CHROMA_AUTH}
      - CHROMA_SERVER_AUTH_PROVIDER=chromadb.auth.token.TokenAuthServerProvider

volumes:
  postgres_data:
  chromadb_data:
  caddy_data:
  caddy_config:
```

### Caddyfile

```
# Caddyfile
{
    email admin@yourdomain.com
}

yourdomain.com {
    # Frontend
    handle {
        reverse_proxy frontend:3000
    }
    
    # API
    handle /api/* {
        reverse_proxy api:8000
    }
    
    # Security headers
    header {
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
    }
}
```

### Option 2: Railway/Fly.io (PaaS)

```bash
# Railway
railway login
railway init
railway add --database postgres
railway up

# Fly.io
fly launch
fly postgres create
fly secrets set OPENROUTER_API_KEY=xxx
fly deploy
```

## CI/CD (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: |
          cd backend
          pip install -e ".[test]"
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ghcr.io/${{ github.repository }}/api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: deploy
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/socratic
            docker-compose pull
            docker-compose up -d
```

## CLI Distribution

### PyPI Package

```bash
# Install globally
pip install socratic-learn

# Or pipx (isolated)
pipx install socratic-learn

# Usage
socratic start "CAP theorem"
socratic answer
socratic analyze
```

### Standalone Binary (optional)

```bash
# Build with PyInstaller
pyinstaller --onefile cli/main.py -n socratic

# Or Nuitka for smaller size
nuitka --standalone --onefile cli/main.py
```

## Environment Variables

```bash
# .env.example

# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/socratic
OPENROUTER_API_KEY=sk-or-xxx
JWT_SECRET=generate-random-string-here

# Optional
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
ENVIRONMENT=development  # development | staging | production
LOG_LEVEL=INFO

# LLM Config
LLM_PROVIDER=openrouter  # openrouter | anthropic | openai
LLM_MODEL=claude-3-5-sonnet
LLM_FALLBACK_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
```

## Monitoring (optional)

```yaml
# Add to docker-compose
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Backup Cron

```bash
# /etc/cron.d/socratic-backup
0 3 * * * root /opt/socratic/backup.sh

# backup.sh
#!/bin/bash
DATE=$(date +%Y-%m-%d)
docker exec postgres pg_dump -U app socratic | gzip > /backups/db-$DATE.sql.gz
tar -czf /backups/chroma-$DATE.tar.gz /data/chromadb
# Upload to S3/B2 (optional)
```

## Health Checks

```bash
# API health endpoint
curl http://localhost:8000/health
# {"status": "healthy", "db": "ok", "chromadb": "ok"}

# Quick check script
#!/bin/bash
if ! curl -sf http://localhost:8000/health > /dev/null; then
    docker-compose restart api
    echo "API restarted" | mail -s "Socratic Alert" admin@domain.com
fi
```






