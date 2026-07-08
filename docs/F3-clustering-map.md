# F3 — Demand clustering + hotspot map

Signals dedupe into Demands ("Drainage — Ward 12 — 47 requests, ↑20%/wk"),
rendered on a constituency map with intensity.

**Status:** heuristic clustering LIVE (same category+ward → same demand, in
`backend/app/services/clustering.py`). Remaining: embedding-based clustering,
trend computation, the actual map.

## Prerequisites

- [ ] F2 embeddings being written (`demand_signals.embedding`)
- [ ] Google Maps JavaScript API key (Google Cloud console → enable
      "Maps JavaScript API" → API key, restrict to the droplet origin
      `http://168.144.24.204:8082`). Free tier covers hackathon usage.
- [ ] `wards` table has `lat/lon` (F4 loader; for the map you can hand-fill
      20 ward centroids from Google Maps in 30 minutes if F4 isn't done)

## Step-by-step

1. **Embedding clustering** (replace the heuristic in `assign_to_demand`):
   ```sql
   SELECT id, 1 - (centroid <=> :emb) AS sim FROM demands
   WHERE category = :cat ORDER BY centroid <=> :emb LIMIT 1;
   ```
   If `sim >= 0.80` → attach to that demand and update its centroid to the
   running mean; else create a new demand with `centroid = :emb`.
   Same ward is a strong prior: try ward-scoped match first at 0.75,
   cross-ward at 0.85 (tune on seed data).
2. **Demand titles**: on creation, one Gemini call: "Title this civic demand
   in ≤6 words from: {summary_en}" → better than `Water — Ward 12`.
3. **Trend**: nightly (or on `/api/works/rerank`) compute
   `trend_7d = (signals last 7d − prior 7d) / max(prior 7d, 1)` per demand
   with one SQL GROUP BY over `demand_signals.created_at`.
4. **Map component** (`frontend/src/App.jsx`, Hotspot Map tab):
   - Load Maps JS API with the key (env: `VITE_MAPS_API_KEY` passed as a
     compose build arg like khanpaan does for its VITE_ vars).
   - Center on the constituency; one `Circle` per demand at its ward's
     lat/lon, radius ∝ `signal_count`, color by category; click → side panel
     with `GET /api/demands/{id}` (sample quotes, trend, photos).
   - Poll `GET /api/demands` every 10s — this is what makes the live demo
     submission "pop in".
5. **Seed data for the demo**: `backend/scripts/seed_demo.py` — ~2,400
   synthetic submissions across 4 languages/20 wards/6 weeks, injected
   through the REAL pipeline (`/api/ingest/demo` in a loop with backdated
   `received_at`). Never insert demands directly — judges may ask to trace
   one from raw message to map.

## Testing

1. **Dedupe quality**: inject 3 phrasings of the same issue
   ("borewell broken", "no water from handpump", "पानी नहीं आ रहा") same ward
   → `SELECT count(*) FROM demands WHERE category='water';` grows by 1, not 3.
2. **Separation**: inject "school roof leaking" same ward → new demand, not
   merged into water.
3. **Cross-ward**: same complaint in two wards → two demands (ward-scoped
   threshold working).
4. **Trend**: seed script backdates properly →
   `SELECT title, trend_7d FROM demands WHERE trend_7d > 0;` returns the
   demands you scripted as "rising".
5. **Map visual**: 20 wards render; largest circle = highest signal_count;
   click opens the detail panel with ≥1 citizen quote.
6. **Live pop-in**: with the map open, inject a demo submission → circle
   grows / appears within one poll cycle (≤10s) with no page refresh.
