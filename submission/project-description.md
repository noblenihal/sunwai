# sunwai (सुनवाई) — copy-paste blurbs for the submission form

## Project name
**sunwai — every voice, on the record**

## One-liner (≤140 chars)
AI that turns WhatsApp voice notes from citizens into evidence-ranked development
priorities for an MP's office — in any Indian language.

## Short description (~100 words)
sunwai is a demand-intelligence engine for constituency development planning
(Track 1: People's Priorities). Citizens send a voice note, photo, or text on
WhatsApp in their own language — no app, no forms, no literacy requirement.
Gemini transcribes, categorizes, and geolocates every submission; identical
demands cluster across languages; and each clustered demand is cross-checked
against Census and government ward data to produce a ranked, evidence-backed
works list the MP can defend publicly. A Silent Needs view flags high-need
wards that aren't submitting — the unheard, not the unneeding — and a public
board shows every citizen what was raised and what got resolved.

## The problem (from the brief)
MPs receive development requests through public meetings, letters, social
media, and grievance portals, while development plans hold dozens of competing
proposals. There is no objective way to consolidate citizen feedback, spot
recurring needs, and weigh proposals against real demand.

## How AI is the actual engine (not decorative)
1. **Structuring** — one Gemini multimodal call per submission: transcribes
   Indic-language audio, reads photos, extracts category/location/urgency,
   returns schema-validated JSON, and rejects non-civic noise.
2. **Clustering** — Gemini embeddings + pgvector cosine similarity merge the
   same demand phrased in Hindi, Devanagari, English, or Bengali into one
   record with a Gemini-written title.
3. **Ranking** — score = submissions × trend × evidence-gap weight (weights
   visible); Gemini writes a 3-sentence justification per top work, citing
   only supplied figures, cached by input hash so unchanged data costs zero.
4. **Conversation** — the WhatsApp bot asks a clarifying question when the
   location is missing and accepts the answer by voice or text, replying in
   the citizen's language with an English footer.

## Evidence layer
Pilot constituency: **South Delhi PC (Kalkaji segment, Govindpuri)** — all 12
wards loaded with official figures from SEC Delhi Delimitation 2022 Annexure-1
(Census 2011 population + SC share). Equity is geographic and Census-based:
we never profile individual submitters. Four expansion constituencies
(Kolkata Dakshin, Ahmedabad East, Mumbai North East, Chennai South) run live
in Bengali, Gujarati, Marathi, and Tamil to demonstrate config-file onboarding.

## Tech stack
Gemini API (multimodal structuring, embeddings, generation) · Google Maps
Platform (hotspot map, OSM fallback) · FastAPI · PostgreSQL + pgvector ·
React · WhatsApp via Twilio Business API (Meta Cloud API in production) ·
Docker Compose on a single VM · GitHub Actions CI/CD

## Deployability & cost (rubric: 25%)
Runs today on one 2GB VM shared with three other apps. Onboarding a new
constituency = one config file (ward list + centroids) — demonstrated live
with 5 constituencies. Estimated run cost at demo scale: **~$5–15/month,
all Gemini**; no per-citizen cost, no hardware, no app installs, no training.

## Inclusivity (rubric: 15%)
Voice-first, any Indian language, works on any phone with WhatsApp; photo
submissions for the non-literate; replies in the citizen's own language.
Silent Needs inverts the usual bias: the system surfaces wards that DON'T
complain. Roadmap: SMS/IVR fallback and assisted kiosks at panchayat offices.

## Impact
One MP represents ~25 lakh citizens; 543 constituencies. The same engine
generalizes to MLA constituencies and municipal wards. Transparency board
closes the loop: the record the MP sees is the record the public sees.

## Live links
- MP dashboard: http://168.144.24.204:8082
- Public board: http://168.144.24.204:8082/board
- One-page MP brief: http://168.144.24.204:8082/api/brief
- Repo: https://github.com/noblenihal/sunwai
