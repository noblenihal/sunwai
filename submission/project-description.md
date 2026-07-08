# Sunwai — copy-paste blurbs for the submission form

## Project name
**Sunwai — every voice, on the record**

## One-liner (≤140 chars)
AI that turns WhatsApp voice notes from citizens into evidence-ranked
development priorities for an MP's office — in any Indian language.

## "Explain your solution" (985 chars — fits a 1000 limit)
> sunwai (सुनवाई) turns scattered citizen voices into evidence an MP can act
> on. Citizens send a voice note, photo, or text on WhatsApp in any Indian
> language — no app, no forms. Gemini transcribes and structures every
> submission (category, location, urgency), filters noise, and asks a
> clarifying question when the location is missing — answerable by voice.
> Identical demands phrased in different languages merge via Gemini
> embeddings + pgvector, so 47 complaints about one drain become a single
> demand with real weight and trend. Each demand is cross-checked against
> official ward data (Census 2011 / SEC Delhi Delimitation 2022) and ranked
> by a visible formula — submissions × trend × evidence gap — with an
> AI-written justification citing only sourced figures. A Silent Needs view
> flags high-need wards that aren't submitting, and a public board shows
> citizens what was raised and what got resolved. Live across 5
> constituencies in 7 languages; a new constituency is one config file.

## The full feature set (live, not planned)
- **WhatsApp intake** (Twilio Business API): voice/photo/text, any Indian
  language; sense filter rejects non-civic noise; missing location triggers a
  clarifying question answerable by voice; replies in the citizen's language
  with an English footer; retry-safe dedupe; sender numbers hashed.
- **AI structuring**: one Gemini multimodal call — transcription,
  category, location, urgency — schema-validated JSON.
- **Clustering**: gemini-embedding-001 + pgvector cosine; same demand across
  Hindi/Hinglish/English/Bengali merges into one record with a live trend.
- **Evidence-ranked works**: score = submissions × trend × evidence gap;
  facts cite Census 2011 / SEC Delimitation 2022; cached Gemini
  justifications (unchanged reranks cost zero).
- **Office-configurable ranking**: sliders for momentum/evidence weights,
  per-category boosts, and plain-language priorities ("water first before
  summer") the AI applies as a bounded ×0.8–1.25 modifier with a visible
  one-line reason.
- **Silent Needs**: silence = need × (1 − voice); high-need low-voice wards
  flagged for field visits.
- **Transparency**: demand status lifecycle (open → in progress → resolved)
  and a public board — the record the MP sees is the record the public sees.
- **View originals**: every English summary flips back to the citizen's
  actual words, per quote or all at once.
- **One-page MP Brief** (print/PDF) for planning meetings.
- **5 constituencies live** — South Delhi (official SEC/Census data) plus
  Kolkata Dakshin, Ahmedabad East, Mumbai North East, Chennai South
  (Bengali/Gujarati/Marathi/Tamil); new constituency = one config file.

## Technologies used
Google Gemini API (multimodal structuring & voice transcription with
structured output; gemini-embedding-001 for clustering; bounded directive
scoring), Google Maps JavaScript API with Leaflet/OpenStreetMap fallback,
Twilio WhatsApp Business API, FastAPI (Python 3.12), PostgreSQL 16 +
pgvector, React 18 (Vite), Caddy, Docker Compose on a DigitalOcean VM,
GitHub Actions CI/CD. Public data: Census 2011, SEC Delhi Delimitation 2022.

## Deployability & cost (rubric: 25%)
Runs today on one shared 2GB VM (~₹1,000/month, shared with other apps).
Onboarding constituency #6 = one config file (ward list + centroids).
Total AI cost at pilot scale: **~$5–15/month**. No apps, no hardware,
no citizen training. Pilot-ready in a real constituency in ~2 weeks.

## Privacy & responsible AI
Sender numbers hashed before storage; individuals never profiled; equity
analysis is geographic and Census-based; every fact cites its source;
approximate data is labeled approximate; the ranking formula and all AI
modifiers are visible on screen.

## Impact
One MP ≈ 25 lakh citizens; 543 constituencies; the same engine generalizes
to MLA constituencies and municipal wards.

## How to test (2 minutes, no setup)

1. **Try the WhatsApp bot from your own phone**: send `join <code>` to
   **+1 415 523 8886** (Twilio sandbox), then send a voice note in any
   Indian language — e.g. *"हमारी गली में स्ट्रीट लाइट खराब है"*. You'll get
   a reply in your language with a reference number. Skip the location and
   the bot asks for it — answer by voice.
2. **Watch it land**: open the dashboard → Hotspot Map (South Delhi).
   Your demand appears within ~10 seconds, clustered if others said the
   same thing. Click it → "View Originals" shows citizens' actual words.
3. **Interrogate a rank**: Ranked Works → any card shows its formula,
   Census-cited facts and AI justification. Open **Ranking Parameters**,
   type a priority like "water issues first", Save & Rerank — watch the
   order change with a visible, bounded modifier.
4. **Check the loop**: Silent Needs (Madangir's story), then the public
   board (/board) — mark a work "Resolved" in the dashboard and see it move.

## Live links
- Landing: http://168.144.24.204:8082
- MP dashboard: http://168.144.24.204:8082/app
- Public board: http://168.144.24.204:8082/board
- MP brief: http://168.144.24.204:8082/api/brief
- Repo: https://github.com/noblenihal/sunwai
