CREATE TABLE IF NOT EXISTS ai_assistant_runs (
    id BIGSERIAL PRIMARY KEY,
    actor_username TEXT NOT NULL,
    safe_message TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'confirmation_required', 'executing', 'failed')),
    assistant_message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_assistant_runs_actor_created
    ON ai_assistant_runs (actor_username, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_assistant_tool_calls (
    id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES ai_assistant_runs(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    policy TEXT NOT NULL CHECK (policy IN ('read_only', 'requires_confirmation')),
    status TEXT NOT NULL CHECK (status IN ('completed', 'confirmation_required', 'executing', 'failed')),
    arguments JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_summary TEXT NOT NULL,
    result_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_assistant_tool_calls_run
    ON ai_assistant_tool_calls (run_id, id);
