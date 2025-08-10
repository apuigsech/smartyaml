SELECT 
    u.id,
    u.username,
    u.email,
    u.created_at,
    u.last_login,
    p.first_name,
    p.last_name
FROM users u
LEFT JOIN profiles p ON u.id = p.user_id
WHERE u.id = ?
AND u.active = true;