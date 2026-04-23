CREATE TABLE IF NOT EXISTS clubs (
    id            SERIAL PRIMARY KEY,
    club_name     TEXT NOT NULL,
    sport         TEXT NOT NULL,
    skill_level   TEXT NOT NULL,
    season        TEXT NOT NULL,
    how_to_join   TEXT,
    instagram     TEXT,
    notes         TEXT,
    photo_url     TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
