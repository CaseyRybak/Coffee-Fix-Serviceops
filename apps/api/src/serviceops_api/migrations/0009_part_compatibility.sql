ALTER TABLE parts_catalog
    ADD COLUMN IF NOT EXISTS part_type TEXT;
ALTER TABLE parts_catalog
    ADD COLUMN IF NOT EXISTS parameter_label TEXT;
ALTER TABLE parts_catalog
    ADD COLUMN IF NOT EXISTS parameter_value TEXT;
ALTER TABLE parts_catalog
    ADD COLUMN IF NOT EXISTS parameter_unit TEXT;
ALTER TABLE parts_catalog
    ADD COLUMN IF NOT EXISTS factual_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_parts_catalog_factual_key
    ON parts_catalog (factual_key)
    WHERE factual_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS part_compatibility (
    id BIGSERIAL PRIMARY KEY,
    part_id BIGINT NOT NULL REFERENCES parts_catalog(id),
    compatibility_level TEXT NOT NULL CHECK (compatibility_level IN ('exact_model', 'series', 'generic_group')),
    brand TEXT,
    model TEXT,
    series TEXT,
    machine_family TEXT,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_part_compatibility_part ON part_compatibility (part_id);
CREATE INDEX IF NOT EXISTS idx_part_compatibility_lookup
    ON part_compatibility (brand, model, series, machine_family);
