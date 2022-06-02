#!/bin/bash

type=${type:-game}

read -r -d '' sql <<SQL
WITH
all_outs AS (
  SELECT
    ground,
    start_date,
    innings,
    team,
    runs
  FROM team_innings
  WHERE all_out
),
forty_wickets AS (
  SELECT
    ground,
    start_date,
    SUM(runs) AS game_runs
  FROM all_outs
  GROUP BY ground, start_date
  HAVING COUNT(*) = 4
),
twenty_wickets AS (
  SELECT
    ground,
    start_date,
    team,
    SUM(runs) AS team_runs
  FROM all_outs
  GROUP BY ground, start_date, team
  HAVING COUNT(*) = 2
),
game_bannermen AS (
  SELECT
    innings.ground,
    innings.start_date,
    innings.player,
    SUM(innings.runs) AS runs,
    MIN(forty_wickets.game_runs) AS game_runs,
    SUM(innings.runs)::numeric(20, 10) / MIN(forty_wickets.game_runs)::numeric(20, 10) AS proportion
  FROM innings
  INNER JOIN forty_wickets ON
    innings.ground = forty_wickets.ground AND
    innings.start_date = forty_wickets.start_date
  GROUP BY
    innings.ground,
    innings.start_date,
    innings.player
),
team_bannermen AS (
  SELECT
    innings.ground,
    innings.start_date,
    innings.team,
    innings.player,
    SUM(innings.runs) AS runs,
    MIN(twenty_wickets.team_runs) AS team_runs,
    SUM(innings.runs)::numeric(20, 10) / MIN(twenty_wickets.team_runs)::numeric(20, 10) AS proportion
  FROM innings
  INNER JOIN twenty_wickets ON
    innings.ground = twenty_wickets.ground AND
    innings.start_date = twenty_wickets.start_date AND
    innings.team = twenty_wickets.team
  GROUP BY
    innings.ground,
    innings.start_date,
    innings.team,
    innings.player
)
SELECT
  ground,
  start_date,
  player,
  runs,
  ${type}_runs,
  proportion::numeric(20, 2)
FROM ${type}_bannermen
WHERE runs IS NOT NULL
ORDER BY proportion DESC
LIMIT 10;
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
