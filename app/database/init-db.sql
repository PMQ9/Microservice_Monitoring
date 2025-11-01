-- Social Media Platform Database Schema

-- Content Creators Table
CREATE TABLE IF NOT EXISTS content_creators (
    id SERIAL PRIMARY KEY,
    creator_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_content INTEGER DEFAULT 0,
    followers INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT FALSE,
    category VARCHAR(50),
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_creators_created_at ON content_creators(created_at);
CREATE INDEX idx_creators_followers ON content_creators(followers);
CREATE INDEX idx_creators_category ON content_creators(category);

-- Content Items Table
CREATE TABLE IF NOT EXISTS content_items (
    id SERIAL PRIMARY KEY,
    content_id VARCHAR(50) UNIQUE NOT NULL,
    creator_id VARCHAR(50) REFERENCES content_creators(creator_id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    views BIGINT DEFAULT 0,
    likes BIGINT DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    shares_count INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    file_size_mb DECIMAL(10,2),
    is_published BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_content_creator_id ON content_items(creator_id);
CREATE INDEX idx_content_type ON content_items(type);
CREATE INDEX idx_content_created_at ON content_items(created_at);
CREATE INDEX idx_content_views ON content_items(views);
CREATE INDEX idx_content_likes ON content_items(likes);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_views BIGINT DEFAULT 0,
    total_likes BIGINT DEFAULT 0,
    session_start TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    user_type VARCHAR(20) DEFAULT 'regular',
    location VARCHAR(100),
    age_group VARCHAR(20)
);

CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_last_activity ON users(last_activity);
CREATE INDEX idx_users_is_active ON users(is_active);

-- User Activity Table (for tracking interactions)
CREATE TABLE IF NOT EXISTS user_activities (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    content_id VARCHAR(50) REFERENCES content_items(content_id) ON DELETE CASCADE,
    activity_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    watch_duration_seconds INTEGER,
    engagement_score DECIMAL(5,2)
);

CREATE INDEX idx_activity_user_id ON user_activities(user_id);
CREATE INDEX idx_activity_content_id ON user_activities(content_id);
CREATE INDEX idx_activity_type ON user_activities(activity_type);
CREATE INDEX idx_activity_created_at ON user_activities(created_at);

-- User Follows Table
CREATE TABLE IF NOT EXISTS user_follows (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    creator_id VARCHAR(50) REFERENCES content_creators(creator_id) ON DELETE CASCADE,
    followed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, creator_id)
);

CREATE INDEX idx_follows_user_id ON user_follows(user_id);
CREATE INDEX idx_follows_creator_id ON user_follows(creator_id);

-- Materialized view for platform statistics (for performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS platform_stats AS
SELECT
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as active_users,
    (SELECT COUNT(*) FROM content_creators) as total_creators,
    (SELECT COUNT(*) FROM content_items) as total_content,
    (SELECT SUM(views) FROM content_items) as total_views,
    (SELECT SUM(likes) FROM content_items) as total_likes,
    (SELECT COUNT(*) FROM user_activities WHERE activity_type = 'view' AND created_at > NOW() - INTERVAL '1 hour') as views_last_hour,
    (SELECT COUNT(*) FROM user_activities WHERE activity_type = 'like' AND created_at > NOW() - INTERVAL '1 hour') as likes_last_hour,
    NOW() as last_updated;

CREATE UNIQUE INDEX ON platform_stats (last_updated);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_platform_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY platform_stats;
END;
$$ LANGUAGE plpgsql;

-- Insert some initial seed data for testing
INSERT INTO content_creators (creator_id, name, bio, followers, verified, category)
VALUES
    ('creator_seed_1', 'Tech Guru', 'Technology reviews and tutorials', 50000, TRUE, 'technology'),
    ('creator_seed_2', 'Fitness Master', 'Health and fitness content', 30000, TRUE, 'fitness'),
    ('creator_seed_3', 'Food Explorer', 'Cooking and food reviews', 45000, FALSE, 'food')
ON CONFLICT (creator_id) DO NOTHING;

INSERT INTO users (user_id, username, email, user_type, age_group, location)
VALUES
    ('user_seed_1', 'john_doe', 'john@example.com', 'premium', '25-34', 'US'),
    ('user_seed_2', 'jane_smith', 'jane@example.com', 'regular', '18-24', 'UK'),
    ('user_seed_3', 'bob_wilson', 'bob@example.com', 'regular', '35-44', 'CA')
ON CONFLICT (user_id) DO NOTHING;
