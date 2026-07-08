# Pitch deck — speaker notes for sunwai-pitch.pptx (6 slides)

> The deck itself is `sunwai-pitch.pptx` (screenshot-led, big type).
> This file = what to SAY on each slide, ~60–75 seconds each.

**Slide 1 — Title**
"This is Sunwai — every voice, on the record. It turns WhatsApp voice notes
from citizens into evidence-ranked development priorities for an MP's office.
What you're seeing is live right now — 378 voices across 5 constituencies in
7 languages." *(Pause. Let the live number land.)*

**Slide 2 — Problem + the loop**
"An MP represents 25 lakh people. Needs arrive as letters, calls, and
lobbying — the loudest voice wins. The brief's own example: school upgrade or
vocational centre? Nobody can answer objectively today. Sunwai's loop: a
citizen SPEAKS on WhatsApp in any language; Gemini STRUCTURES it; we WEIGH it
against Census data; the office ACTS and the public sees it."

**Slide 3 — The engine**
"Left: the live demand map of South Delhi. Right: the part I'm proudest of —
55 reports about one blocked drain, in Hindi, Hinglish, and English, merged
into ONE demand by embedding clustering. The office can flip any summary back
to the citizen's original words. That's demand, deduplicated — real counts,
not noise." *(If demoing live: send a voice note here.)*

**Slide 4 — Defensible and steerable**
"Every rank shows its arithmetic: 45 submissions × 4.5 trend × 2.13 evidence
gap — the facts cite Census 2011 and the SEC delimitation order, and the
justification is AI-written from ONLY those figures. And the office holds the
dials: weights, category boosts, or priorities typed in plain language —
'water first before summer' — which the AI applies as a bounded, visible
modifier. Steerable, never a black box."

**Slide 5 — Silence + transparency**
"Madangir: 44% Scheduled Caste, a resettlement colony, and just 3 submissions
from 52,000 people. Silent Needs flags it for a field visit — AI that listens
is good; AI that notices who ISN'T speaking is governance. And everything the
MP sees, the public sees: raised, in progress, resolved, on a public board."

**Slide 6 — Deploy + ask**
"All of this runs on one ₹1,000-a-month server. Five constituencies are live
— onboarding a new one is one config file. Total AI cost at pilot scale:
five to fifteen dollars a month. The ask: pilot Sunwai in one constituency
for 90 days — success is every rupee of the next MPLADS allocation traceable
to ranked, evidenced public demand. Thank you."

## Likely judge Q&A
- **"Why is #1 above #2?"** → point at the formula on slide 4; recompute live.
- **"What stops spam campaigns?"** → sender hashing + dedupe today; campaign
  detection (burst/similarity analysis) is roadmap; evidence weighting already
  dampens pure volume.
- **"Where does caste data come from?"** → geographic Census aggregates only;
  individuals never profiled (privacy line on the public board footer).
- **"Real WhatsApp?"** → yes, Twilio Business API sandbox; direct Meta Cloud
  API in production. Live demo available on request.
- **"Expansion cities' data?"** → Delhi runs official SEC/Census figures;
  expansion wards carry labeled approximate estimates until their official
  loads — that's the onboarding step we'd do in week one of a pilot.
