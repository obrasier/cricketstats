#!/bin/bash

pg_ctl start > /dev/null
createdb default > /dev/null

gender=${gender:-men}
format=test

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
outs AS (
  SELECT
    ground,
    start_date,
    player,
    team,
    runs,
    pos,
    innings,
    CASE WHEN not_out THEN 0 ELSE 1 END AS outs
  FROM innings
),
ten_wickets AS (
  SELECT
    ground,
    start_date,
    team,
    innings,
    SUM(runs) AS team_runs
  FROM outs
  GROUP BY ground, start_date, team, innings
  HAVING SUM(outs) = 10
),
bannermen_by_position AS (
  SELECT
    innings.ground,
    innings.start_date,
    innings.team,
    innings.player,
    innings.pos,
    innings.innings,
    SUM(innings.runs) AS runs,
    MIN(ten_wickets.team_runs) AS team_runs,
    SUM(innings.runs)::numeric(20, 10) / MIN(ten_wickets.team_runs)::numeric(20, 10) AS proportion
  FROM innings
  INNER JOIN ten_wickets ON
    innings.ground = ten_wickets.ground AND
    innings.start_date = ten_wickets.start_date AND
    innings.team = ten_wickets.team AND
    innings.innings = ten_wickets.innings
  GROUP BY
    innings.ground,
    innings.start_date,
    innings.team,
    innings.player,
    innings.pos,
    innings.innings
)
SELECT *
FROM (
  SELECT
    pos,
    row_number() OVER (PARTITION BY pos ORDER BY proportion DESC) AS rank,
    ground,
    start_date,
    player,
    runs,
    team_runs,
    proportion::numeric(20, 2)
  FROM bannermen_by_position
  WHERE runs IS NOT NULL
) ranked
WHERE rank <= 3 AND pos BETWEEN 3 and 11
ORDER BY pos, rank;

DROP TABLE innings;
SQL

echo "${sql}" | psql -q -d default

dropdb default > /dev/null
pg_ctl stop > /dev/null
