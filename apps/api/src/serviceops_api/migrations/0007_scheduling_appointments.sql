CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE IF NOT EXISTS request_appointments (
    id BIGSERIAL PRIMARY KEY,
    service_request_id BIGINT NOT NULL REFERENCES service_requests(id),
    technician_identifier TEXT NOT NULL,
    technician_name TEXT NOT NULL,
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    window_label TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('scheduled', 'rescheduled', 'cancelled')),
    reschedule_reason TEXT,
    cancel_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (ends_at > starts_at)
);

CREATE INDEX IF NOT EXISTS idx_request_appointments_request
    ON request_appointments (service_request_id);
CREATE INDEX IF NOT EXISTS idx_request_appointments_technician_window
    ON request_appointments (technician_identifier, starts_at, ends_at, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_request_appointments_one_active_per_request
    ON request_appointments (service_request_id)
    WHERE status = 'scheduled';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'request_appointments_no_overlap'
    ) THEN
        ALTER TABLE request_appointments
            ADD CONSTRAINT request_appointments_no_overlap
            EXCLUDE USING gist (
                technician_identifier WITH =,
                tstzrange(starts_at, ends_at, '[)') WITH &&
            )
            WHERE (status = 'scheduled');
    END IF;
END $$;
