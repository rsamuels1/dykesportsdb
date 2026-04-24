CREATE TABLE IF NOT EXISTS clubs (
    id            SERIAL PRIMARY KEY,
    club_name     TEXT NOT NULL,
    sport         TEXT NOT NULL,
    city          TEXT,
    is_comp       BOOLEAN NOT NULL DEFAULT FALSE,
    is_rec        BOOLEAN NOT NULL DEFAULT FALSE,
    is_pickup     BOOLEAN NOT NULL DEFAULT FALSE,
    is_league     BOOLEAN NOT NULL DEFAULT FALSE,
    is_tournament BOOLEAN NOT NULL DEFAULT FALSE,
    is_travel          BOOLEAN NOT NULL DEFAULT FALSE,
    is_trans_inclusive  BOOLEAN NOT NULL DEFAULT FALSE,
    is_lesbian_centered BOOLEAN NOT NULL DEFAULT FALSE,
    weekday       TEXT,
    cost          TEXT,
    contact       TEXT,
    how_to_join   TEXT,
    instagram     TEXT,
    website       TEXT,
    notes         TEXT,
    photo_url     TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO clubs (club_name, sport, city, instagram, website, is_pickup, cost, weekday, is_comp, is_rec, notes, status)
VALUES (
    'Dyke Soccer',
    'Soccer',
    'Portland',
    'dykesoccerpdx',
    'https://dykesoccer.com',
    TRUE,
    'Free',
    'Saturdays',
    FALSE,
    TRUE,
    '🌈 🏳️‍⚧️For queer women, trans and gender-expansive folks, + 4 whom this is home ⚽️💦 est. April 2022',
    'approved'
);
