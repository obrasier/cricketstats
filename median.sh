#!/bin/bash

pg_ctl start > /dev/null
createdb default > /dev/null

gender=${gender:-men}
format=${format:-test}
min_runs=${min_runs:-1000}

read -r -d '' sql <<SQL
CREATE TABLE innings (
  index integer,
  player text,
  team text,
  runs integer,
  runs_txt text,
  not_out boolean,
  mins numeric,
  bf numeric,
  fours numeric,
  sixes numeric,
  sr numeric,
  pos integer,
  innings integer,
  opposition text,
  ground text,
  start_date date
);

COPY innings
FROM '$(pwd)/data/${gender}_${format}_batting.csv'
WITH (FORMAT csv, HEADER);

WITH
first_38 AS (
  SELECT *
  FROM (
    SELECT
      ROW_NUMBER() OVER (PARTITION BY player, team ORDER BY start_date ASC, innings ASC) AS seq,
      *
    FROM
      innings
  ) with_seq
  WHERE seq <= 38
),
medians AS (
  SELECT
    player,
    team,
    MIN(start_date) AS debut,
    SUM(runs) AS total,
    PERCENTILE_CONT(0.5) WITHIN GROUP(ORDER BY runs) AS median,
    SUM(runs)::numeric(20, 10) / SUM(CASE WHEN not_out THEN 0 ELSE 1 END)::numeric(20, 10) AS average,
    SUM(CASE WHEN not_out THEN 0 ELSE 1 END) AS outs,
    SUM(CASE WHEN runs >= 50 AND runs < 100 THEN 1 ELSE 0 END) AS fifties,
    SUM(CASE WHEN runs >= 100 THEN 1 ELSE 0 END) AS hundreds,
    MAX(runs) AS high_score,
    COUNT(*) AS innings,
    STDDEV_SAMP(runs) AS stddev,
    SUM(CASE WHEN runs <= 10 THEN 1 ELSE 0 END) AS under10
  FROM innings
  WHERE runs IS NOT NULL
  GROUP BY player, team
  HAVING SUM(CASE WHEN not_out THEN 0 ELSE 1 END) > 0
)
SELECT
  player,
  team,
  debut,
  total,
  average::numeric(20, 2) AS average,
  median::numeric(20, 2) AS median,
  (average - median)::numeric(20, 2) AS diff,
  (average / median)::numeric(20, 2) AS ratio
FROM medians
WHERE average < median AND total > 200
ORDER BY total DESC
LIMIT 100;

DROP TABLE innings;
SQL

echo "${sql}" | psql -q -d default

dropdb default > /dev/null
pg_ctl stop > /dev/null
