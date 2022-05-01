#!/bin/bash

min_runs=${min_runs:-1000}

read -r -d '' sql <<SQL
WITH
averages AS (
  SELECT
    player,
    SUM(runs) AS total_runs,
    SUM(CASE WHEN not_out THEN 0 ELSE 1 END) AS outs,
    SUM(runs)::numeric(20, 10) / SUM(CASE WHEN not_out THEN 0 ELSE 1 END)::numeric(20, 10) AS average
  FROM innings
  GROUP BY player
)
SELECT player, total_runs, outs, average::numeric(20, 2)
FROM averages
WHERE average::numeric(20, 2) = average::numeric(20, 0)
  AND total_runs > ${min_runs}
ORDER BY total_runs DESC;
SQL

dir="$(dirname "${BASH_SOURCE[0]}")"

"${dir}/run_sql.sh" "${sql}"
