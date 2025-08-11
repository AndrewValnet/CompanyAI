-- Enable pgvector (one-time)
CREATE EXTENSION IF NOT EXISTS vector;

-- 1) Companies master
CREATE TABLE IF NOT EXISTS companies (
  company_id        BIGSERIAL PRIMARY KEY,
  domain            TEXT UNIQUE NOT NULL,
  name              TEXT,
  website_url       TEXT,
  country           TEXT,
  industry          TEXT,
  employee_range    TEXT,
  tech_tags         TEXT[],        -- optional: ["shopify","react","stripe"]
  created_at        TIMESTAMPTZ DEFAULT now(),
  updated_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ON companies ((lower(domain)));

-- 2) Similarweb monthly metrics (wide-ish fact)
CREATE TABLE IF NOT EXISTS company_metrics_monthly (
  company_id        BIGINT REFERENCES companies(company_id),
  month             DATE NOT NULL,         -- first day of month
  country           TEXT NOT NULL,         -- 'WW','US','CA',...
  visits            DOUBLE PRECISION,
  pages_per_visit   DOUBLE PRECISION,
  avg_visit_secs    DOUBLE PRECISION,
  bounce_rate       DOUBLE PRECISION,
  page_views        DOUBLE PRECISION,
  load_ts           TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (company_id, month, country)
);
CREATE INDEX ON company_metrics_monthly (month);
CREATE INDEX ON company_metrics_monthly (country);

-- 3) Lists (flexible named buckets)
CREATE TABLE IF NOT EXISTS lists (
  list_id   BIGSERIAL PRIMARY KEY,
  slug      TEXT UNIQUE NOT NULL,   -- e.g., 'interested', 'reached_out'
  name      TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO lists (slug, name) 
VALUES ('interested','Interested Companies'), ('reached_out','Reached Out')
ON CONFLICT (slug) DO NOTHING;

-- 4) Memberships (many-to-many so you can keep history & multi-bucket if needed)
CREATE TABLE IF NOT EXISTS list_memberships (
  list_id     BIGINT REFERENCES lists(list_id),
  company_id  BIGINT REFERENCES companies(company_id),
  added_at    TIMESTAMPTZ DEFAULT now(),
  removed_at  TIMESTAMPTZ,
  added_by    TEXT,
  removed_by  TEXT,
  PRIMARY KEY (list_id, company_id, added_at)
);
CREATE INDEX ON list_memberships (company_id);
CREATE INDEX ON list_memberships (list_id);

-- Helper view: current members (not removed)
CREATE OR REPLACE VIEW list_members_current AS
SELECT lm.list_id, lm.company_id, lm.added_at
FROM list_memberships lm
WHERE lm.removed_at IS NULL;

-- 5) Status audit (optional but nice to have)
CREATE TABLE IF NOT EXISTS company_status_history (
  company_id  BIGINT REFERENCES companies(company_id),
  from_status TEXT,
  to_status   TEXT,
  changed_at  TIMESTAMPTZ DEFAULT now(),
  changed_by  TEXT
);
CREATE INDEX ON company_status_history (company_id, changed_at);

-- 6) Embeddings for semantic search
-- Choose dimension to match your embedding model (e.g., 1536)
CREATE TABLE IF NOT EXISTS company_embeddings (
  company_id  BIGINT PRIMARY KEY REFERENCES companies(company_id),
  embedding   VECTOR(1536),
  -- text used for embedding: name + tagline + about + tech tags + notes
  source_text TEXT
);
CREATE INDEX company_embeddings_hnsw ON company_embeddings
USING hnsw (embedding vector_l2_ops);
