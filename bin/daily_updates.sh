#!/bin/bash
source /usr/local/bin/pg-env.sh 8.4
cat /home/filmaster/film20/film20/sql/daily_updates.sql | psql -U film20 -p justenter film20 -h psycho
