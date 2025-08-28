-- Get Users Query
-- Retrieve users with pagination and optional filtering

SELECT
    u.id,
    u.name,
    u.email,
    u.created_at,
    u.updated_at,
    u.status,
    p.avatar_url,
    COUNT(o.id) as order_count
FROM users u
LEFT JOIN profiles p ON u.id = p.user_id
LEFT JOIN orders o ON u.id = o.user_id
WHERE
    u.deleted_at IS NULL
    AND (
        :search_term IS NULL
        OR u.name ILIKE '%' || :search_term || '%'
        OR u.email ILIKE '%' || :search_term || '%'
    )
    AND (
        :status IS NULL
        OR u.status = :status
    )
GROUP BY u.id, u.name, u.email, u.created_at, u.updated_at, u.status, p.avatar_url
ORDER BY
    CASE WHEN :sort_by = 'name' THEN u.name END ASC,
    CASE WHEN :sort_by = 'email' THEN u.email END ASC,
    CASE WHEN :sort_by = 'created_at' THEN u.created_at END DESC,
    u.id ASC
LIMIT :limit OFFSET :offset;
