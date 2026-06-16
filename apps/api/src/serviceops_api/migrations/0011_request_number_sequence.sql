CREATE SEQUENCE IF NOT EXISTS service_request_number_seq;

SELECT setval('service_request_number_seq',
    GREATEST(
        COALESCE(
            (
                SELECT MAX((substring(request_number from '^[^-]+-[0-9]{8}-([0-9]+)$'))::bigint)
                FROM service_requests
                WHERE request_number ~ '^[^-]+-[0-9]{8}-[0-9]+$'
            ),
            0
        ),
        1
    ),
    EXISTS (SELECT 1 FROM service_requests)
);
