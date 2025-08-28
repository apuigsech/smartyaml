-- Update User Query
-- Update user information with validation and audit trail

WITH updated_user AS (
    UPDATE users
    SET
        name = COALESCE(:name, name),
        email = COALESCE(:email, email),
        status = COALESCE(:status, status),
        updated_at = NOW(),
        updated_by = :updated_by_user_id
    WHERE
        id = :user_id
        AND deleted_at IS NULL
    RETURNING *
),
updated_profile AS (
    UPDATE profiles
    SET
        first_name = CASE
            WHEN :name IS NOT NULL
            THEN SPLIT_PART(:name, ' ', 1)
            ELSE first_name
        END,
        last_name = CASE
            WHEN :name IS NOT NULL AND ARRAY_LENGTH(STRING_TO_ARRAY(:name, ' '), 1) > 1
            THEN SUBSTRING(:name FROM POSITION(' ' IN :name) + 1)
            WHEN :name IS NOT NULL
            THEN ''
            ELSE last_name
        END,
        bio = COALESCE(:bio, bio),
        avatar_url = COALESCE(:avatar_url, avatar_url),
        phone = COALESCE(:phone, phone),
        updated_at = NOW()
    WHERE user_id = :user_id
    RETURNING *
),
audit_log AS (
    INSERT INTO user_audit_log (
        user_id,
        action,
        changed_fields,
        old_values,
        new_values,
        changed_by,
        created_at
    )
    SELECT
        :user_id,
        'update',
        ARRAY[:changed_fields],
        :old_values::jsonb,
        :new_values::jsonb,
        :updated_by_user_id,
        NOW()
    WHERE :user_id IS NOT NULL
    RETURNING id
)
SELECT
    u.id,
    u.name,
    u.email,
    u.status,
    u.created_at,
    u.updated_at,
    p.first_name,
    p.last_name,
    p.bio,
    p.avatar_url,
    p.phone
FROM updated_user u
LEFT JOIN updated_profile p ON u.id = p.user_id;
