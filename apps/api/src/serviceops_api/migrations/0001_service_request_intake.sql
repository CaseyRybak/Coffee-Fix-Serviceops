CREATE TABLE customers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    telegram TEXT,
    client_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_customers_phone ON customers (phone);

CREATE TABLE machines (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    brand TEXT NOT NULL,
    model TEXT,
    location_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_machines_customer_id ON machines (customer_id);
CREATE INDEX idx_machines_brand ON machines (brand);

CREATE TABLE service_requests (
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

CREATE INDEX idx_service_requests_customer_id ON service_requests (customer_id);
CREATE INDEX idx_service_requests_status ON service_requests (status);
CREATE INDEX idx_service_requests_created_at ON service_requests (created_at);

CREATE TABLE attachment_metadata (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attachment_metadata_service_request_id ON attachment_metadata (service_request_id);
