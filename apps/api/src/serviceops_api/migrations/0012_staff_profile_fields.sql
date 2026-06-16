ALTER TABLE staff_accounts
    ADD COLUMN IF NOT EXISTS first_name TEXT NOT NULL DEFAULT '';

ALTER TABLE staff_accounts
    ADD COLUMN IF NOT EXISTS last_name TEXT NOT NULL DEFAULT '';

ALTER TABLE staff_accounts
    ADD COLUMN IF NOT EXISTS phone TEXT NOT NULL DEFAULT '';

UPDATE staff_accounts
SET first_name = display_name
WHERE first_name = '' AND last_name = '' AND display_name <> '';
