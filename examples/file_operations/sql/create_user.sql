-- Create User Query
-- Insert a new user with validation and return the created user

WITH new_user AS (
    INSERT INTO users (
        name,
        email,
        password_hash,
        status,
        created_at,
        updated_at
    ) VALUES (
        :name,
        :email,
        :password_hash,
        COALESCE(:status, 'active'),
        NOW(),
        NOW()
    )
    RETURNING *
),
new_profile AS (
    INSERT INTO profiles (
        user_id,
        first_name,
        last_name,
        created_at,
        updated_at
    )
    SELECT
        nu.id,
        SPLIT_PART(:name, ' ', 1) as first_name,
        CASE
            WHEN ARRAY_LENGTH(STRING_TO_ARRAY(:name, ' '), 1) > 1
            THEN SUBSTRING(:name FROM POSITION(' ' IN :name) + 1)
            ELSE ''
        END as last_name,
        NOW(),
        NOW()
    FROM new_user nu
    RETURNING *
)
SELECT
    u.id,
    u.name,
    u.email,
    u.status,
    u.created_at,
    u.updated_at,
    p.first_name,
    p.last_name
FROM new_user u
JOIN new_profile p ON u.id = p.user_id;
