-- Migration: replace skill_level/play_type/season with boolean columns
-- Run this against your Neon DB before deploying updated app code.

-- 1. Add new boolean columns
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS is_comp       BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS is_rec        BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS is_pickup     BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS is_league     BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS is_tournament BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE clubs ADD COLUMN IF NOT EXISTS is_travel     BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Migrate skill_level → is_comp / is_rec
UPDATE clubs SET is_comp = TRUE WHERE skill_level ILIKE 'competitive';
UPDATE clubs SET is_rec  = TRUE WHERE skill_level ILIKE 'recreational';
UPDATE clubs SET is_comp = TRUE, is_rec = TRUE WHERE skill_level ILIKE 'all%';

-- 3. Migrate play_type → is_pickup / is_league / is_tournament / is_travel
UPDATE clubs SET is_pickup     = TRUE WHERE play_type ILIKE '%pick%';
UPDATE clubs SET is_league     = TRUE WHERE play_type ILIKE '%league%';
UPDATE clubs SET is_tournament = TRUE WHERE play_type ILIKE '%tournament%';
UPDATE clubs SET is_travel     = TRUE WHERE play_type ILIKE '%travel%';
-- "both" typically means pick-up + league
UPDATE clubs SET is_pickup = TRUE, is_league = TRUE WHERE play_type ILIKE '%both%';
-- default to pick-up if nothing mapped
UPDATE clubs SET is_pickup = TRUE
WHERE NOT is_pickup AND NOT is_league AND NOT is_tournament AND NOT is_travel
  AND play_type IS NOT NULL AND play_type != '';

-- 4. Drop old columns
ALTER TABLE clubs DROP COLUMN IF EXISTS season;
ALTER TABLE clubs DROP COLUMN IF EXISTS skill_level;
ALTER TABLE clubs DROP COLUMN IF EXISTS play_type;
