CREATE TABLE IF NOT EXISTS notification_delivery_attempts (
    id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    request_number TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'sent', 'failed', 'retried')),
    channel TEXT,
    provider_message_id TEXT,
    error TEXT,
    attempt_count INTEGER NOT NULL DEFAULT 1 CHECK (attempt_count > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_notification_delivery_request
    ON notification_delivery_attempts (request_number);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_status
    ON notification_delivery_attempts (status);
CREATE INDEX IF NOT EXISTS idx_notification_delivery_event_type
    ON notification_delivery_attempts (event_type);
