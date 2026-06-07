CREATE TABLE IF NOT EXISTS ai_suggestions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_number TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    rationale TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    source_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ai_suggestions_request_number ON ai_suggestions (request_number);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_status ON ai_suggestions (status);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_kind ON ai_suggestions (kind);
CREATE INDEX IF NOT EXISTS idx_ai_suggestions_created_at ON ai_suggestions (created_at);
