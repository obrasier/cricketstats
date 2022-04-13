#!/bin/bash

min_runs=${min_runs:-1000}

read -r -d '' sql <<SQL
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
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
