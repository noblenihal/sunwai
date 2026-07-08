# sunwai — feature build docs

Base platform (deployed): compose stack on the droplet (`db` pgvector, `api`
FastAPI, `web` Caddy+React on :8082), GitHub Actions auto-deploy on push to
`main`, working pipeline: ingest → Gemini structuring → cluster → rank.

| # | Feature | Doc | Status |
|---|---------|-----|--------|
| F1 | WhatsApp intake (voice/text/photo) | [F1-whatsapp-intake.md](F1-whatsapp-intake.md) | webhook stubbed |
| F2 | AI structuring of submissions | [F2-structuring.md](F2-structuring.md) | **text done**; voice+image pending |
| F3 | Clustering + hotspot map | [F3-clustering-map.md](F3-clustering-map.md) | heuristic done; embeddings+map pending |
| F4 | Evidence fusion (public data) | [F4-evidence-fusion.md](F4-evidence-fusion.md) | schema ready; data load pending |
| F5 | Ranked works + justifications | [F5-ranked-works.md](F5-ranked-works.md) | scoring done; Gemini justifications pending |
| F6 | Silent Needs tab | [F6-silent-needs.md](F6-silent-needs.md) | endpoint done; scoring pending |
| F7 | MP Brief PDF export | [F7-mp-brief-pdf.md](F7-mp-brief-pdf.md) | not started |

Recommended build order: **F2 (finish) → F3 → F5 → F4 → F6 → F7 → F1**.

## Conventions used in every doc

- All API paths are relative to `http://168.144.24.204:8082` (prod) or
  `http://localhost:8082` (local compose).
- `$DEMO_TOKEN` = `DEMO_INJECT_TOKEN` from `/opt/sunwai/.env.local`.
- "Redeploy" always means: commit → push to `main` → Actions deploys →
  `gh run watch` until green.
- Test SQL runs via:
  `docker exec sunwai-db-1 psql -U postgres -d sunwai -c "<sql>"`
