#!/bin/bash

read -r -d '' sql <<SQL
WITH
all_outs AS (
  SELECT
    ground,
    start_date,
    innings,
    team,
    opposition,
    runs
  FROM team_innings
  WHERE all_out
),
bowling_bannermen AS (
  SELECT
    all_outs.team AS batting_team,
    all_outs.opposition AS bowling_team,
    all_outs.ground,
    all_outs.start_date,
    all_outs.innings,
    all_outs.runs AS team_total,
    bowling_innings.player,
    bowling_innings.runs::numeric(20, 0) AS runs_conceded,
    (bowling_innings.runs::numeric(20, 10) / all_outs.runs::numeric(20, 10))::numeric(20, 2) AS proportion
  FROM bowling_innings
  INNER JOIN all_outs ON
    bowling_innings.ground = all_outs.ground AND
    bowling_innings.start_date = all_outs.start_date AND
    bowling_innings.team = all_outs.opposition AND
    bowling_innings.innings = all_outs.innings
  WHERE bowling_innings.runs IS NOT NULL
)
SELECT
  batting_team,
  bowling_team,
  ground,
  start_date,
  innings,
  team_total,
  player,
  runs_conceded,
  proportion::numeric(20, 2)
FROM bowling_bannermen
ORDER BY proportion DESC
LIMIT 10;
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
