# सुनवाई sunwai — every voice, on the record

**AI demand-intelligence for constituency development planning.**
Built for *Build with AI: Code for Communities* — Track 1: People's Priorities.

Citizens talk to WhatsApp in any Indian language. MPs look at a dashboard.
In between sits an engine that converts noise into evidence.

**Live:** [MP dashboard](http://168.144.24.204:8082) ·
[Public transparency board](http://168.144.24.204:8082/board) ·
[One-page MP brief](http://168.144.24.204:8082/api/brief)

## What it does

- **WhatsApp intake** — voice note, photo, or text, any Indian language.
  No app, no forms. The bot asks a clarifying question when the location is
  missing (and accepts the answer by voice), filters non-civic noise, and
  replies in the citizen's language.
- **AI structuring** — one Gemini multimodal call transcribes, categorizes,
  geolocates, and grades urgency; schema-validated output.
- **Clustering** — Gemini embeddings + pgvector merge the same demand across
  languages into one record with a real count and trend.
- **Evidence-ranked works** — `score = submissions × trend × evidence gap`,
  facts sourced from SEC Delhi Delimitation 2022 / Census 2011, with a cached
  Gemini-written justification per work.
- **Silent Needs** — `silence = need × (1 − voice)` flags high-need wards
  that aren't submitting: unheard, not unneeding.
- **Transparency board** — public page of what's raised / in progress /
  resolved, same record the MP sees.
- **5 constituencies, 7 languages** — South Delhi (official-data pilot) plus
  Kolkata Dakshin, Ahmedabad East, Mumbai North East, Chennai South;
  onboarding a constituency is one config file.

## Architecture

```
WhatsApp (Twilio) ──┐
demo/seed intake ───┤→ STRUCTURE (Gemini multimodal, schema-validated)
                    │→ CLUSTER   (gemini-embedding-001 + pgvector cosine)
                    │→ ENRICH    (Census/SEC ward data, BigQuery-ready)
                    │→ SCORE     (visible formula + cached justifications)
                    ▼
   MP dashboard (React+Maps) · Public board · Print-ready MP brief
```

Stack: FastAPI · PostgreSQL+pgvector · React (Vite) · Caddy · Gemini API ·
Google Maps (OSM fallback) · Docker Compose on one 2GB VM · GitHub Actions CD.

## How to test (no setup)

1. **WhatsApp**: send `join mistake-won` to **+1 415 523 8886**, then a voice
   note in any Indian language. No location? The bot asks — answer by voice.
2. Open the [dashboard](http://168.144.24.204:8082/app): your demand appears
   on the map in ~10s. Click it → *View Originals* for citizens' real words.
3. *Ranked Works* → open **Ranking Parameters**, type "water issues first",
   Save & Rerank — the order changes with a visible, bounded AI modifier.
4. Mark a work *Resolved* → watch it move on the
   [public board](http://168.144.24.204:8082/board).

## Run it

```bash
cp .env.example .env.local   # add GEMINI_API_KEY (only hard requirement)
docker compose --env-file .env.local up --build
# dashboard http://localhost:8082 · board /board · api docs /api/docs
```

Seed a living constituency:
`docker compose exec api python -m app.scripts.seed_demo --fresh`

## Repo map

- `backend/app/services/` — the engine: structuring → clustering → evidence → ranking
- `backend/app/routers/` — API + WhatsApp webhook + public board + brief
- `backend/initdb/` — schema, official ward data, constituencies
- `frontend/` — dashboard + public board ("Register" design system)
- `docs/` — per-feature build docs (F1–F7)
- `submission/` — hackathon submission kit

Privacy: sender numbers are hashed before storage; equity analysis is
geographic and Census-based — individuals are never profiled.
