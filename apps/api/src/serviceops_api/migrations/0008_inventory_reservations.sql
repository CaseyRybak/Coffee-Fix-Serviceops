ALTER TABLE stock_counts
    ADD COLUMN IF NOT EXISTS low_stock_threshold INTEGER CHECK (low_stock_threshold IS NULL OR low_stock_threshold >= 0);

CREATE TABLE IF NOT EXISTS part_reservations (
    id BIGSERIAL PRIMARY KEY,
    request_number TEXT NOT NULL,
    appointment_id BIGINT,
    part_id BIGINT NOT NULL REFERENCES parts_catalog(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status TEXT NOT NULL CHECK (status IN ('active', 'released', 'consumed')),
    note TEXT,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id BIGSERIAL PRIMARY KEY,
    part_id BIGINT NOT NULL REFERENCES parts_catalog(id),
    movement_type TEXT NOT NULL CHECK (
        movement_type IN ('manual_adjustment', 'reservation_created', 'reservation_adjusted', 'release', 'consumption')
    ),
    quantity INTEGER NOT NULL,
    quantity_on_hand_after INTEGER NOT NULL CHECK (quantity_on_hand_after >= 0),
    reserved_quantity_after INTEGER NOT NULL CHECK (reserved_quantity_after >= 0),
    available_quantity_after INTEGER NOT NULL CHECK (available_quantity_after >= 0),
    request_number TEXT,
    reservation_id BIGINT REFERENCES part_reservations(id),
    note TEXT,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_part_reservations_request ON part_reservations (request_number);
CREATE INDEX IF NOT EXISTS idx_part_reservations_part_status ON part_reservations (part_id, status);
CREATE INDEX IF NOT EXISTS idx_stock_movements_part ON stock_movements (part_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_request ON stock_movements (request_number);
