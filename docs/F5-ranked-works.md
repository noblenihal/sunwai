# F5 — Ranked Works list with explainable scoring

The core output: development works ranked by
`score = signal_count × (1 + trend_7d) × gap_weight`, each with an evidence
card and a Gemini-written plain-language justification. Weights stay visible
— the MP must be able to defend "#1 over #7" publicly.

**Status:** scoring + rank LIVE (`backend/app/services/ranking.py`);
justifications and the full evidence-card UI pending.

## Prerequisites

- [ ] F4 loaded (real `gap_weight` instead of the 1.5/1.0 placeholder)
- [ ] F3 trend computation writing `trend_7d`
- [x] `gemini-pro-latest` reachable with the existing key

## Step-by-step

1. **Real gap weight**: in `rerank_all`, use `evidence["gap_score"]`:
   `gap_weight = 1 + gap_score` (range 1..3). Keep the three factors as
   columns in the API response so the UI can show the arithmetic.
2. **Justifications** (batch, AFTER ranks are assigned): for the top 15
   demands, one Gemini call each:
   - Input: title, signal_count, trend, 3 sample citizen quotes
     (translated), evidence `facts`, rank context ("this ranked #3 of 40").
   - Prompt: "Write 3 sentences for an MP's office explaining why this work
     deserves priority. Cite the numbers. No flattery, no hedging."
   - Store in `demands.justification`. Skip demands whose inputs are
     unchanged since the last run (hash inputs → `justification_key` column)
     to keep rerank cheap and idempotent.
3. **Rerank trigger**: keep `POST /api/works/rerank` manual for the demo
   (click a "Recompute" button — judges like seeing it), plus a cron
   container or host crontab hitting it nightly.
4. **Evidence card UI** (Ranked Works tab): expandable card per work —
   rank, title, the three factor numbers with the formula, evidence facts as
   bullet list, sample quotes, justification paragraph. Add a small
   "weights" popover documenting the formula verbatim.
5. Redeploy.

## Testing

1. **Determinism**: call `/api/works/rerank` twice with no new data → ranks
   and scores identical both times.
2. **Formula check** (do this by hand once): pick a work, verify
   `score == signal_count * (1 + trend) * gap_weight` from the API fields.
3. **Ordering flip**: inject 5 quick submissions for a mid-ranked demand →
   rerank → its rank improves; nothing else moves erratically.
4. **Justification quality gate**: read all top-10 justifications aloud —
   each must cite ≥2 concrete numbers and contain zero invented facts
   (cross-check against the evidence card). Any hallucinated number →
   tighten the prompt ("Use ONLY the figures provided").
5. **Idempotent LLM spend**: rerank twice → second run makes 0 Gemini calls
   (check api logs for the skip message).
6. **UI**: expanding card #1 shows formula numbers that multiply out to the
   shown score.
