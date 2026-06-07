CREATE TABLE IF NOT EXISTS staff_accounts (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS staff_account_roles (
    staff_account_id BIGINT NOT NULL REFERENCES staff_accounts(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'dispatcher', 'technician', 'inventory')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (staff_account_id, role)
);

CREATE TABLE IF NOT EXISTS staff_audit_events (
    id BIGSERIAL PRIMARY KEY,
    actor_username TEXT NOT NULL,
    target_username TEXT NOT NULL,
    action TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_staff_accounts_active ON staff_accounts(active);
CREATE INDEX IF NOT EXISTS idx_staff_account_roles_role ON staff_account_roles(role);
CREATE INDEX IF NOT EXISTS idx_staff_audit_target ON staff_audit_events(target_username);
CREATE INDEX IF NOT EXISTS idx_staff_audit_action ON staff_audit_events(action);
