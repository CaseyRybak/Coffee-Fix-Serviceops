CREATE TABLE IF NOT EXISTS parts_catalog (
    id BIGSERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    unit TEXT NOT NULL,
    compatibility_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stock_counts (
    part_id BIGINT PRIMARY KEY REFERENCES parts_catalog(id),
    quantity_on_hand INTEGER NOT NULL CHECK (quantity_on_hand >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS request_parts_used (
    id BIGSERIAL PRIMARY KEY,
    request_number TEXT NOT NULL,
    part_id BIGINT NOT NULL REFERENCES parts_catalog(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    stock_after_use INTEGER NOT NULL DEFAULT 0 CHECK (stock_after_use >= 0),
    note TEXT,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE request_parts_used
    ADD COLUMN IF NOT EXISTS stock_after_use INTEGER NOT NULL DEFAULT 0 CHECK (stock_after_use >= 0);

CREATE INDEX IF NOT EXISTS idx_parts_catalog_sku ON parts_catalog (sku);
CREATE INDEX IF NOT EXISTS idx_request_parts_used_request_number ON request_parts_used (request_number);
CREATE INDEX IF NOT EXISTS idx_request_parts_used_part_id ON request_parts_used (part_id);

CREATE TABLE IF NOT EXISTS technician_diagnoses (
    id BIGSERIAL PRIMARY KEY,
    request_number TEXT NOT NULL,
    machine_powered_on BOOLEAN NOT NULL,
    water_supply_checked BOOLEAN NOT NULL,
    leak_checked BOOLEAN NOT NULL,
    error_code_checked BOOLEAN NOT NULL,
    summary TEXT NOT NULL,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS technician_repair_results (
    id BIGSERIAL PRIMARY KEY,
    request_number TEXT NOT NULL,
    result TEXT NOT NULL,
    summary TEXT NOT NULL,
    next_step TEXT,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_technician_diagnoses_request_number ON technician_diagnoses (request_number);
CREATE INDEX IF NOT EXISTS idx_technician_repair_results_request_number ON technician_repair_results (request_number);
