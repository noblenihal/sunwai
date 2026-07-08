# sunwai (सुनवाई)

**AI demand-intelligence engine for constituency development planning.**
Built for *Build with AI: Code for Communities* — Track 1: People's Priorities.

Citizens talk to WhatsApp. MPs look at a dashboard. In between sits an engine
that converts noise into evidence.

## Architecture

```
Citizen (voice/text/photo, any language)
   → WhatsApp webhook            backend/app/routers/whatsapp.py
   → STRUCTURE  (Gemini)         backend/app/services/structuring.py
   → AGGREGATE  (cluster/dedupe) backend/app/services/clustering.py
   → ENRICH     (public data)    backend/app/services/evidence.py
   → SCORE      (ranked works)   backend/app/services/ranking.py
   → MP dashboard (map, ranked works, silent needs)   frontend/
```

## Stack

- `db` — Postgres 16 + pgvector (demand signals, clusters, ward evidence)
- `api` — FastAPI + google-genai (structuring, clustering, ranking)
- `web` — React (Vite) dashboard, served by Caddy, `/api/*` proxied to `api`

## Local dev

```bash
cp .env.example .env.local   # fill in values
docker compose up --build
# dashboard: http://localhost:8082   api: http://localhost:8082/api/health
```

## Deploy

Push to `main` → GitHub Actions SSHes into the droplet →
`/opt/sunwai`: `git pull && docker compose up -d --build`.
Live at http://168.144.24.204:8082
