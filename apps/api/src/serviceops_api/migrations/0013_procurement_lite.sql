ALTER TABLE stock_movements
    DROP CONSTRAINT IF EXISTS stock_movements_movement_type_check;

ALTER TABLE stock_movements
    ADD CONSTRAINT stock_movements_movement_type_check CHECK (
        movement_type IN (
            'manual_adjustment',
            'reservation_created',
            'reservation_adjusted',
            'release',
            'consumption',
            'procurement_receipt'
        )
    );

CREATE TABLE IF NOT EXISTS procurement_suppliers (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    contact_name TEXT,
    phone TEXT,
    email TEXT,
    note TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    actor TEXT NOT NULL DEFAULT 'inventory',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS purchase_requests (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT NOT NULL REFERENCES procurement_suppliers(id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'pending_approval', 'approved', 'ordered', 'received', 'cancelled')),
    note TEXT,
    actor TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS purchase_request_items (
    id BIGSERIAL PRIMARY KEY,
    purchase_request_id BIGINT NOT NULL REFERENCES purchase_requests(id) ON DELETE CASCADE,
    part_id BIGINT NOT NULL REFERENCES parts_catalog(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    note TEXT
);

CREATE INDEX IF NOT EXISTS idx_purchase_requests_supplier_id ON purchase_requests(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_requests_status ON purchase_requests(status);
CREATE INDEX IF NOT EXISTS idx_purchase_request_items_request_id ON purchase_request_items(purchase_request_id);
CREATE INDEX IF NOT EXISTS idx_purchase_request_items_part_id ON purchase_request_items(part_id);
