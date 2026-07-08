# sunwai — feature build docs

Base platform (deployed): compose stack on the droplet (`db` pgvector, `api`
FastAPI, `web` Caddy+React on :8082), GitHub Actions auto-deploy on push to
`main`, working pipeline: ingest → Gemini structuring → cluster → rank.

| # | Feature | Doc | Status |
|---|---------|-----|--------|
| F1 | WhatsApp intake (Twilio) | [F1-whatsapp-intake.md](F1-whatsapp-intake.md) | **code live**; needs Twilio account + webhook URL set |
| F2 | AI structuring of submissions | [F2-structuring.md](F2-structuring.md) | ✅ text/voice/photo, ward resolution, embeddings |
| F3 | Clustering + hotspot map | [F3-clustering-map.md](F3-clustering-map.md) | ✅ embedding clustering, trends, Google Map |
| F4 | Evidence fusion (public data) | [F4-evidence-fusion.md](F4-evidence-fusion.md) | ✅ 12 wards, Census 2011 / SEC 2022 data |
| F5 | Ranked works + justifications | [F5-ranked-works.md](F5-ranked-works.md) | ✅ gap-weighted scoring, cached Flash justifications |
| F6 | Silent Needs tab | [F6-silent-needs.md](F6-silent-needs.md) | ✅ silence = need × (1−voice), field-visit flags |
| F7 | MP Brief export | [F7-mp-brief-pdf.md](F7-mp-brief-pdf.md) | ✅ print-CSS brief at /api/brief |

Remaining to go fully live: create Twilio account → set sandbox webhook to
`http://168.144.24.204:8082/api/whatsapp/webhook` → send `join <code>` from
a phone → WhatsApp a voice note.

## Conventions used in every doc

- All API paths are relative to `http://168.144.24.204:8082` (prod) or
  `http://localhost:8082` (local compose).
- `$DEMO_TOKEN` = `DEMO_INJECT_TOKEN` from `/opt/sunwai/.env.local`.
- "Redeploy" always means: commit → push to `main` → Actions deploys →
  `gh run watch` until green.
- Test SQL runs via:
  `docker exec sunwai-db-1 psql -U postgres -d sunwai -c "<sql>"`
