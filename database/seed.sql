INSERT INTO users (email, full_name, hashed_password, role)
VALUES
    ('founder@venturemind.ai', 'Demo Founder', 'seed-with-backend-script-for-bcrypt', 'user'),
    ('admin@venturemind.ai', 'Demo Admin', 'seed-with-backend-script-for-bcrypt', 'admin')
ON CONFLICT (email) DO NOTHING;
