#!/bin/bash

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
bannermen_by_position AS (
  SELECT
    innings.ground,
    innings.start_date,
    innings.team,
    innings.player,
    innings.pos,
    innings.innings,
    innings.runs AS runs,
    all_outs.runs AS team_runs,
    (innings.runs::numeric(20, 10) / all_outs.runs::numeric(20, 10))::numeric(20, 2) AS proportion
  FROM innings
  INNER JOIN all_outs ON
    innings.ground = all_outs.ground AND
    innings.start_date = all_outs.start_date AND
    innings.team = all_outs.team AND
    innings.innings = all_outs.innings
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
    proportion
  FROM bannermen_by_position
  WHERE runs IS NOT NULL
) ranked
WHERE rank <= 3 AND pos BETWEEN 3 and 11
ORDER BY pos, rank;
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
