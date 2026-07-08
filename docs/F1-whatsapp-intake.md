# F1 — WhatsApp intake (voice, text, photo)

Citizen sends a voice note / text / photo to a WhatsApp number; sunwai stores
it as a `submission`, runs the pipeline, and replies with a confirmation in
the citizen's language.

Build this LAST — everything else demos via `/api/ingest/demo`.

## Channel decision (2026-07-08)

**Twilio WhatsApp Sandbox** — user's Facebook access is blocked, so the Meta
Cloud API path is out. Twilio needs no Meta account (email+phone signup,
free trial), supports inbound voice/photo media, allows plain-HTTP webhooks
(no tunnel needed), and demos via a join-code: participants WhatsApp
`join <code>` to the shared sandbox number, then talk to sunwai.
Production story for the pitch: direct Meta WhatsApp Business API.

## Prerequisites

- [ ] Twilio account (twilio.com — email + phone verify, no card for trial)
- [ ] From Console → Messaging → Try it out → "Send a WhatsApp message":
      note the sandbox number + join code; set
      "When a message comes in" = `http://168.144.24.204:8082/api/whatsapp/webhook`
- [ ] `TWILIO_ACCOUNT_SID` (AC…) + `TWILIO_AUTH_TOKEN` into
      `/opt/sunwai/.env.local` (auth token needed to download media URLs
      and validate webhook signatures)
- [ ] F2 complete (structuring handles text at minimum) — DONE

## Step-by-step

1. **Env**: fill the three `WHATSAPP_*` vars in `/opt/sunwai/.env.local`,
   `docker compose --env-file .env.local up -d api` to reload.
2. **Webhook verification** is already implemented
   (`GET /api/whatsapp/webhook` in `backend/app/routers/whatsapp.py`
   handles Meta's `hub.challenge` handshake). In the Meta dashboard →
   WhatsApp → Configuration → set Callback URL to
   `https://<tunnel-or-domain>/api/whatsapp/webhook` + your verify token →
   Verify and Save → subscribe to the `messages` field.
3. **Implement `POST /api/whatsapp/webhook`** (currently a stub):
   - Parse `entry[0].changes[0].value.messages[0]`; ignore status callbacks
     (payloads with `statuses`).
   - `type == "text"` → `raw_text = message.text.body`, `kind = "text"`.
   - `type == "audio" | "image"` → call
     `GET https://graph.facebook.com/v21.0/{media_id}` (Bearer access token)
     to get the media URL, download it (same Bearer), store to
     `/data/media/` volume, set `media_url`, `kind = "voice" | "image"`.
   - Hash the sender: `sender_hash = sha256(wa_id)[:16]` — never store the
     raw phone number.
   - Insert into `submissions` (channel `whatsapp`), then call
     `structuring.process_submission(db, submission_id)`.
   - **Reply within seconds** (Meta expects HTTP 200 fast — do the pipeline
     in a FastAPI `BackgroundTasks` if Gemini is slow): send
     `POST /v21.0/{PHONE_NUMBER_ID}/messages` with a body like:
     `"Got it ✓ Category: {category}. Reference #S{submission_id}."`
     translated to `signal.language` via Gemini/Translation API.
4. **Dedupe retries**: Meta redelivers on non-200. Store
   `message.id` (wamid) in a `wa_message_ids` table with a UNIQUE constraint;
   skip if already present.
5. Redeploy.

## Testing

1. **Handshake**: after step 2, Meta dashboard shows the webhook as Verified
   (green). Manual check:
   `curl "https://<url>/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<token>&hub.challenge=42"`
   → responds `42`.
2. **Text round-trip**: from an allow-listed phone, WhatsApp "पानी की समस्या
   रामपुर में" to the test number → within ~5s you receive a Hindi
   confirmation with a reference ID.
3. **DB check**: `SELECT channel, kind, language FROM submissions ORDER BY id DESC LIMIT 1;`
   → `whatsapp | text | hi`. Matching row in `demand_signals`.
4. **Voice note**: send one → `kind = voice`, media file exists in the
   volume, signal has a sensible `summary_en` (requires F2 voice done).
5. **Retry safety**: resend the same webhook payload with
   `curl -X POST .../api/whatsapp/webhook -d @payload.json` twice → only one
   submission row.
6. **Dashboard**: the new demand appears on the map tab without refresh
   (Firestore-style polling is fine: the tabs refetch on focus).
