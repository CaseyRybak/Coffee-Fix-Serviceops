CREATE TABLE IF NOT EXISTS technician_profiles (
    staff_username TEXT PRIMARY KEY REFERENCES staff_accounts(username) ON DELETE CASCADE,
    active BOOLEAN NOT NULL DEFAULT true,
    skill_brands JSONB NOT NULL DEFAULT '[]'::jsonb,
    service_regions JSONB NOT NULL DEFAULT '[]'::jsonb,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_technician_profiles_active
    ON technician_profiles (active);
