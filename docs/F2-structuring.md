# F2 — AI structuring of submissions

Raw citizen input (any language; text / voice / photo) → structured
`DemandSignal {category, sub_type, location_text, urgency, summary_en, language}`.

**Status: text path is LIVE** (`backend/app/services/structuring.py`, Gemini
structured-output schema `_SIGNAL_SCHEMA`). Remaining: voice, image, ward
resolution, embeddings.

## Prerequisites

- [x] `GEMINI_API_KEY` in droplet `.env.local` (done — shared with khanpaan)
- [ ] For voice: Speech-to-Text — decide between Gemini multimodal audio
      (zero extra setup, good Indic support — RECOMMENDED for hackathon) vs
      Cloud Speech-to-Text (needs a GCP service account JSON)
- [ ] For ward resolution: `wards` table loaded (F4) with ward names/aliases

## Step-by-step

1. **Voice** (in `process_submission`): when `sub.kind == "voice"`, read the
   media file and pass audio bytes to Gemini alongside `EXTRACTION_PROMPT`:
   ```python
   contents=[EXTRACTION_PROMPT,
             genai.types.Part.from_bytes(data=audio, mime_type="audio/ogg")]
   ```
   (WhatsApp voice notes are ogg/opus — Gemini accepts them directly.)
   Ask the schema for one extra field `transcript` and store it in
   `submissions.raw_text` so reprocessing never needs the audio again.
2. **Image**: same pattern with `mime_type="image/jpeg"`; prompt addition:
   "The citizen sent a photo. Describe the civic issue it shows."
3. **Ward resolution**: after extraction, resolve `location_text` →
   `ward_code`: exact/fuzzy match against `wards.name` + an `aliases` list
   (SQL `ILIKE` first, then Gemini "which of these wards is meant?" with the
   ward list in-context — it's small). Write `ward_code` onto the signal.
4. **Embedding**: call `client.models.embed_content(model=settings.embedding_model,
   contents=summary_en)` → `UPDATE demand_signals SET embedding = :vec`.
   Powers F3 clustering.
5. **Hardening** (post-MVP, note in pitch): Gemini call retries with
   exponential backoff; on repeated failure keep the submission with
   `processed_at NULL` and add a `/api/ingest/reprocess` sweep endpoint.
6. Redeploy.

## Testing

1. **Text (already passing in prod)**:
   ```bash
   curl -s -X POST localhost:8082/api/ingest/demo \
     -H "content-type: application/json" -H "x-demo-token: $DEMO_TOKEN" \
     -d '{"kind":"text","raw_text":"हमारे गांव रामपुर में बोरवेल खराब है"}'
   ```
   Expect: `category=water`, `language=hi`, English `summary_en`, urgency 1–5.
2. **Schema safety**: send gibberish ("asdf 123") → must still return valid
   JSON with `category=other`, never a 500.
3. **Voice**: `{"kind":"voice","media_url":"/data/media/test.ogg"}` with a
   Hindi test recording → signal fields populated + transcript stored.
   Record 3 test clips (Hindi, Telugu, English) and keep them in
   `backend/testdata/`.
4. **Image**: photo of a pothole → `category=road`; photo of garbage heap →
   `category=drainage` or `other` (accept either, assert not `school`).
5. **Ward resolution**: text mentioning a real ward name → `ward_code` set:
   `SELECT ward_code FROM demand_signals ORDER BY id DESC LIMIT 1;`
6. **Embedding**: `SELECT count(*) FROM demand_signals WHERE embedding IS NULL;`
   → 0 after a batch of injections.
7. **Latency**: time 10 sequential text ingests; p95 must stay under ~4s
   (WhatsApp reply budget in F1).
