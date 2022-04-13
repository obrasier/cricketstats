#!/bin/bash

pg_ctl start > /dev/null
createdb default > /dev/null

gender=${gender:-men}
format=${format:-test}

absolute_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
FROM '${absolute_dir}/../data/${gender}_${format}_batting.csv'
WITH (FORMAT csv, HEADER);

$1

DROP TABLE innings;
SQL

echo "${sql}" | psql -q -d default

dropdb default > /dev/null
pg_ctl stop > /dev/null