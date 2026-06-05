CREATE TABLE IF NOT EXISTS customers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    telegram TEXT,
    client_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers (phone);

CREATE TABLE IF NOT EXISTS machines (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    brand TEXT NOT NULL,
    model TEXT,
    location_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_machines_customer_id ON machines (customer_id);
CREATE INDEX IF NOT EXISTS idx_machines_brand ON machines (brand);

CREATE TABLE IF NOT EXISTS service_requests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    request_number TEXT NOT NULL UNIQUE,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    machine_id BIGINT NOT NULL REFERENCES machines(id),
    status TEXT NOT NULL,
    problem TEXT NOT NULL,
    address TEXT NOT NULL,
    urgency TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_service_requests_customer_id ON service_requests (customer_id);
CREATE INDEX IF NOT EXISTS idx_service_requests_status ON service_requests (status);
CREATE INDEX IF NOT EXISTS idx_service_requests_created_at ON service_requests (created_at);

ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS assigned_technician_name TEXT;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS assigned_technician_phone TEXT;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS assigned_technician_region TEXT;
ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS visit_window TEXT;

CREATE TABLE IF NOT EXISTS attachment_metadata (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_attachment_metadata_service_request_id ON attachment_metadata (service_request_id);

CREATE TABLE IF NOT EXISTS status_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_status_events_service_request_id ON status_events (service_request_id);
CREATE INDEX IF NOT EXISTS idx_status_events_created_at ON status_events (created_at);

CREATE TABLE IF NOT EXISTS clarification_questions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    question TEXT NOT NULL,
    answer TEXT,
    answered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clarification_questions_service_request_id ON clarification_questions (service_request_id);

CREATE TABLE IF NOT EXISTS public_access_tokens (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL UNIQUE REFERENCES service_requests(id),
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_public_access_tokens_token ON public_access_tokens (token);

CREATE TABLE IF NOT EXISTS telegram_opt_ins (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    telegram TEXT,
    token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_telegram_opt_ins_service_request_id ON telegram_opt_ins (service_request_id);
CREATE INDEX IF NOT EXISTS idx_telegram_opt_ins_token ON telegram_opt_ins (token);

CREATE TABLE IF NOT EXISTS internal_notes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    note TEXT NOT NULL,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_internal_notes_service_request_id ON internal_notes (service_request_id);
