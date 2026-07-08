# F4 — Evidence fusion (public data, one real constituency)

Each Demand gets joined with ward-level facts (Census demographics, UDISE
schools/enrollment, health facility registry) so ranking argues from
evidence, not just volume.

**Status:** `wards` table + `evidence_for()` service exist
(`backend/app/services/evidence.py`); no data loaded yet.

## Prerequisites

- [ ] **Pick the constituency** (blocker for everything here — pick one you
      know personally; you'll narrate it on stage)
- [ ] Download extracts:
      - Census 2011 PCA (village/ward level) — data.gov.in or
        censusindia.gov.in; columns: population, SC/ST population, literacy
      - UDISE+ school directory for the district — udiseplus.gov.in
        (school name, lat/lon, enrollment)
      - National Health Facility Registry / district PHC-CHC list —
        facility name, type, lat/lon
- [ ] Ward/village boundary decision: full GIS shapefiles are OVERKILL —
      use ward centroids (lat/lon) + nearest-centroid assignment
- [ ] Python locally with pandas (`pip install pandas openpyxl`)

## Step-by-step

1. **Normalize** in `backend/scripts/load_public_data.py`:
   read the 3 raw files → produce one row per ward:
   `ward_code, name, lat, lon, population, sc_st_share, indicators JSONB`
   where `indicators = {"schools": n, "total_enrollment": n,
   "nearest_phc_km": x, "literacy": x, "piped_water_pct": x, ...}` —
   keep raw source files in `backend/data-raw/` (gitignored if large).
2. **Load**: script writes via `INSERT ... ON CONFLICT (ward_code) DO UPDATE`
   using DATABASE_URL; run it once locally against the droplet DB
   (`ssh -L 5432` tunnel) or bake a `docker compose run api python -m
   scripts.load_public_data` path.
3. **Category-specific gap analysis** in `evidence_for()` — replace the TODO:
   - `school` → enrollment vs capacity, distance to nearest school
   - `water` → piped-water %, groundwater/handpump counts if available
   - `health` → distance to nearest PHC, population per PHC
   - `road`/`drainage` → fall back to population + generic indicators
   Return `{available, gap_score (0..2), facts: [human-readable strings]}` —
   `facts` feed both the evidence card UI and the F5 justification prompt.
4. **Aliases for ward resolution (feeds F2)**: add `aliases TEXT[]` with
   common spellings/localities per ward while you're in the data.
5. Redeploy + run loader.

## Testing

1. **Load count**: `SELECT count(*) FROM wards;` = expected ward count;
   spot-check 3 wards you know: name, population, school count look right.
2. **No orphan geography**: after a seed run,
   `SELECT count(*) FROM demand_signals WHERE ward_code IS NOT NULL AND
   ward_code NOT IN (SELECT ward_code FROM wards);` → 0.
3. **Gap sanity**: pick the ward you KNOW has no nearby school → its
   `evidence_for` on a school demand returns high gap_score and a fact like
   "nearest govt school 4.2 km". Pick a well-served ward → low gap_score.
4. **API surface**: `curl localhost:8082/api/works` → each work's `evidence`
   is `{available: true, facts: [...]}` not `{available: false}`.
5. **The school-vs-vocational-centre rehearsal** (the judges' own example):
   inject competing demands in one ward and verify the evidence facts let
   you argue the comparison out loud convincingly.
