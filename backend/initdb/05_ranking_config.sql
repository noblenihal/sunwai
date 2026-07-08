-- Per-constituency ranking parameters, editable by the MP's office (F5+).
CREATE TABLE IF NOT EXISTS ranking_config (
    constituency    TEXT PRIMARY KEY REFERENCES constituencies(code),
    trend_weight    REAL NOT NULL DEFAULT 1,    -- 0..2: how much momentum matters
    evidence_weight REAL NOT NULL DEFAULT 1,    -- 0..2: how much the data gap matters
    category_boosts JSONB NOT NULL DEFAULT '{}',-- {"water": 1.5, ...} 0.5..2
    directives      TEXT NOT NULL DEFAULT '',   -- plain-language office priorities
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- AI directive modifier cache on demands
ALTER TABLE demands ADD COLUMN IF NOT EXISTS directive_modifier REAL;
ALTER TABLE demands ADD COLUMN IF NOT EXISTS directive_note TEXT;
ALTER TABLE demands ADD COLUMN IF NOT EXISTS directive_key TEXT;
