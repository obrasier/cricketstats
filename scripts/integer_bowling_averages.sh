#!/bin/bash

min_wickets=${min_wickets:-50}

read -r -d '' sql <<SQL
WITH
averages AS (
  SELECT
    player,
    SUM(runs)::numeric(20, 0) AS total_conceded,
    SUM(wickets)::numeric(20, 0) AS wickets,
    SUM(runs)::numeric(20, 10) / SUM(wickets)::numeric(20, 10) AS average
  FROM bowling_innings
  GROUP BY player
)
SELECT player, wickets, total_conceded, average::numeric(20, 2)
FROM averages
WHERE average::numeric(20, 2) = average::numeric(20, 0)
  AND wickets > ${min_wickets}
ORDER BY wickets DESC;
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
