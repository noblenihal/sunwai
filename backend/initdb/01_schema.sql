CREATE EXTENSION IF NOT EXISTS vector;

-- raw inbound messages, exactly as received (audit trail + reprocessing)
CREATE TABLE submissions (
    id            BIGSERIAL PRIMARY KEY,
    channel       TEXT NOT NULL DEFAULT 'whatsapp',   -- whatsapp | demo
    sender_hash   TEXT,                               -- hashed phone, never raw
    kind          TEXT NOT NULL,                      -- voice | text | image
    raw_text      TEXT,                               -- text body or ASR transcript
    media_url     TEXT,
    language      TEXT,
    received_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at  TIMESTAMPTZ
);

-- one structured signal per submission (Gemini output, stage 1)
CREATE TABLE demand_signals (
    id            BIGSERIAL PRIMARY KEY,
    submission_id BIGINT NOT NULL REFERENCES submissions(id),
    category      TEXT NOT NULL,        -- road | water | school | health | drainage | electricity | other
    sub_type      TEXT,
    ward_code     TEXT,                 -- resolved geography
    location_text TEXT,                 -- as stated by citizen
    urgency       SMALLINT,             -- 1..5
    summary_en    TEXT NOT NULL,
    embedding     vector(768),          -- for clustering
    demand_id     BIGINT,               -- FK set once clustered
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- clustered, deduped needs (stage 2) — the unit MPs see
CREATE TABLE demands (
    id            BIGSERIAL PRIMARY KEY,
    title         TEXT NOT NULL,        -- "Drainage — Ward 12"
    category      TEXT NOT NULL,
    ward_code     TEXT,
    signal_count  INT NOT NULL DEFAULT 0,
    trend_7d      REAL,                 -- week-over-week growth
    centroid      vector(768),
    -- stage 3 + 4 outputs
    evidence      JSONB,                -- joined public-data facts
    score         REAL,
    rank          INT,
    justification TEXT,                 -- Gemini-written "why"
    justification_key TEXT,             -- input hash; unchanged inputs skip the LLM call
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE demand_signals
    ADD CONSTRAINT fk_signal_demand FOREIGN KEY (demand_id) REFERENCES demands(id);

-- ward-level public data (Census / UDISE / facility registry), loaded once
CREATE TABLE wards (
    ward_code     TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    aliases       TEXT[],
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    population    INT,
    sc_st_share   REAL,
    indicators    JSONB   -- {schools:[], enrollment:, phc_distance_km:, ...}
);

CREATE INDEX idx_signals_demand ON demand_signals(demand_id);
CREATE INDEX idx_demands_rank ON demands(rank);
