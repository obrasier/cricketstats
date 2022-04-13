#!/bin/bash

min_runs=${min_runs:-100}

read -r -d '' sql <<SQL
WITH
by_player AS (
  SELECT
    date_part('year', start_date) AS year,
    team,
    player,
    SUM(runs) AS runs,
    SUM(CASE WHEN not_out THEN 0 ELSE 1 END) AS outs
  FROM innings
  GROUP BY year, team, player
),
by_team AS (
  SELECT
    year,
    team,
    SUM(runs) AS runs,
    SUM(outs) AS outs
  FROM by_player
  GROUP BY year, team
)
SELECT
  by_player.year,
  by_player.team,
  by_player.player,
  SUM(by_player.runs) AS player_runs,
  (SUM(by_player.runs)::numeric(20, 10) / SUM(by_player.outs)::numeric(20, 10))::numeric(20, 2) AS player_average,
  SUM(by_team.runs) AS team_runs,
  (SUM(by_team.runs)::numeric(20, 10) / SUM(by_team.outs)::numeric(20, 10))::numeric(20, 2) AS team_average,
  (SUM(by_player.runs)::numeric(20, 10) / SUM(by_team.runs)::numeric(20, 10))::numeric(20, 2) AS proportion
FROM by_player
INNER JOIN by_team ON
  by_player.year = by_team.year AND
  by_player.team = by_team.team
WHERE by_player.runs IS NOT NULL
  AND by_team.runs IS NOT NULL
  AND by_player.outs > 0
  AND by_player.runs > ${min_runs}
GROUP BY
  by_player.year,
  by_player.team,
  by_player.player
ORDER BY proportion DESC
LIMIT 10;
SQL

./run_sql.sh "${sql}"
