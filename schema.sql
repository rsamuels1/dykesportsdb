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

INSERT INTO clubs (club_name, sport, city, instagram, website, play_type, cost, weekday, skill_level, season, notes, status)
VALUES (
    'Dyke Soccer',
    'Soccer',
    'Portland',
    'dykesoccerpdx',
    'https://dykesoccer.com',
    'pick-up',
    'Free',
    'Saturdays',
    'All Levels',
    'Seasonal',
    '🌈 🏳️‍⚧️For queer women, trans and gender-expansive folks, + 4 whom this is home ⚽️💦 est. April 2022',
    'img/dykesoccer.png'
    'approved'
);