#!/bin/bash
python run_compute_film_comparators.py
export PGPASSWORD=justenter
source /usr/local/bin/pg-env.sh 8.4
cat load_data.sql | psql -U film20 film20 -h psycho
