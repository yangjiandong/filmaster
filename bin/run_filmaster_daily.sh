#!/bin/bash
#cd /home/apps/filmasterpl/filmaster-stable
NOW=$(date +"%y-%m-%d-%H-%M")
#./run_compute_probable_scores2.sh
#NOW=$(date +"%y-%m-%d-%H-%M")
#./run_compute_film_comparators.sh
#bin/daily_updates.sh
#./run_amazonka_import.sh
#./run_amazonka_export.sh
cd film20
python manage.py update_popularity -v 0
python manage.py fetch_synopses_daily -v 0
python manage.py remove_unused_tags -v 0
python manage.py update_ranking -v 0
NOW=$(date +"%y-%m-%d-%H-%M")
