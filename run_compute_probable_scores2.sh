#!/bin/bash
export PGPASSWORD=justenter
source /usr/local/bin/pg-env.sh 8.4
# cd /home/apps/filmasterpl/filmaster-stable 
python run_compute_probable_scores2.py
