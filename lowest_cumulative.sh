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
cumulative AS (
  SELECT
    player,
    runs,
    SUM(runs) OVER (PARTITION BY player ORDER BY start_date, innings) AS cumulative_runs,
    SUM(CASE WHEN not_out THEN 0 ELSE 1 END) OVER (PARTITION BY player ORDER BY start_date, innings) AS cumulative_outs
  FROM innings
  ORDER BY player, start_date, innings
),
averages AS (
  SELECT
    player,
    runs,
    cumulative_runs::numeric(20, 10) / cumulative_outs::numeric(20, 10) AS cumulative_average
  FROM cumulative
  WHERE cumulative_outs > 0
),
lowest_cumulative_averages AS (
  SELECT
    player,
    SUM(runs) AS total_runs,
    MIN(cumulative_average) AS lowest_cumulative_average
  FROM averages
  GROUP BY player
)
SELECT player, total_runs, lowest_cumulative_average::numeric(20, 2)
FROM lowest_cumulative_averages
WHERE total_runs > ${min_runs}
ORDER BY lowest_cumulative_average DESC
LIMIT 10;

DROP TABLE innings;
SQL

echo $sql | psql -q -d default

dropdb default > /dev/null
pg_ctl stop > /dev/null
