#!/bin/bash

read -r -d '' sql <<SQL
WITH
running AS (
  SELECT
    player,
    MAX(runs) OVER (PARTITION BY player ORDER BY start_date, innings) AS cumulative_high_score,
    COUNT(*) OVER (PARTITION BY player ORDER BY start_date, innings) AS innings_count
  FROM innings
  WHERE runs IS NOT NULL
  ORDER BY player, start_date, innings
),
lowest AS (
  SELECT
    innings_count,
    MIN(cumulative_high_score) AS lowest_high_score
  FROM running
  GROUP BY innings_count
)
SELECT
  lowest.innings_count AS innings,
  player,
  lowest_high_score AS high_score
FROM lowest
INNER JOIN running ON cumulative_high_score = lowest_high_score
  AND running.innings_count = lowest.innings_count
WHERE lowest.innings_count IN (10, 25, 50, 100, 200, 300)
ORDER BY lowest.innings_count;
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
