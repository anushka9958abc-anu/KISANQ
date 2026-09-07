-- Enable on PostgreSQL / MeghRaj / AWS RDS when PostGIS is available
CREATE EXTENSION IF NOT EXISTS postgis;

ALTER TABLE centres ADD COLUMN IF NOT EXISTS geom geography(Point, 4326);
UPDATE centres SET geom = ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography WHERE geom IS NULL;
CREATE INDEX IF NOT EXISTS centres_geom_gix ON centres USING GIST (geom);

-- Nearby centres example:
-- SELECT id, name, ST_Distance(geom, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography) AS meters
-- FROM centres ORDER BY geom <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography;
