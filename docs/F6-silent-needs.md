# F6 — Silent Needs tab

Wards with poor objective indicators but near-zero submissions — flagged as
"unheard, not unneeding", with a suggested field-visit list. The
judge-differentiator: AI that notices who ISN'T speaking.

**Status:** `GET /api/silent-needs` returns wards ordered by submission
count; needs a real silence score + UI.

## Prerequisites

- [ ] F4 loaded (`wards.indicators` + population)
- [ ] Enough seeded signals that per-ward counts vary (F3 seed script)

## Step-by-step

1. **Silence score** (SQL or small service fn):
   `need = normalized composite of bad indicators` (e.g. z-scores of
   nearest_phc_km, 1−literacy, 1−piped_water_pct, averaged 0..1) and
   `voice = ward signal_count / population, normalized 0..1` →
   `silence_score = need × (1 − voice)`.
   Return top wards by `silence_score`, with the 2–3 indicator facts that
   drove `need`.
2. **Exclude noise**: ignore wards with population < a floor (tiny hamlets
   distort normalization); document the floor in the API response.
3. **UI**: third tab — ranked ward cards: name, silence_score as a quiet
   badge ("likely unheard"), the driving facts, signal count vs constituency
   median, and a "suggest field visit" line. Keep the tone factual — this
   tab is about absence of data, so NO invented specifics.
4. **One Gemini touch** (optional, cheap): a 2-sentence "why this ward may
   be silent" note constrained to the provided facts (distance, literacy,
   connectivity) — label it clearly as a hypothesis.
5. Redeploy.

## Testing

1. **Construction check**: seed a ward with bad indicators + 0 submissions →
   it must appear in the top 3 silent needs.
2. **Counter-check**: a ward with bad indicators but MANY submissions must
   NOT appear high (it's heard, just needy — that's F5's job).
3. **Counter-check 2**: a well-off ward with 0 submissions scores low
   (nothing to hear).
4. **Population floor**: hamlet under the floor absent from results;
   API response includes the floor value.
5. **No hallucination**: every fact string on the tab traces to a column in
   `wards.indicators` — grep the API response against the DB row for 3 wards.
6. **Narrative rehearsal**: the tab must support the demo line "AI that
   listens is good; AI that notices who isn't speaking is governance" —
   show a teammate the tab cold; they should get it without explanation.
