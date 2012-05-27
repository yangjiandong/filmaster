#!/bin/bash
test1=`ps x | grep "python run_import_ratings.py" | grep -v grep | awk '{ print $3 }' | grep -ic "S"`
test2=`ps x | grep "python /home/filmaster/film20/fetcher/imdb_fetcher.py" | grep -v grep | awk '{ print $3 }' | grep -ic "S"`
if [ $test1 -eq 0 ]
then
    if [ $test2 -eq 0 ]
    then
        cd /home/filmaster/film20
        python /home/filmaster/film20/run_import_ratings.py
        python /home/filmaster/film20/fetcher/imdb_fetcher.py -f > /dev/null 2>&1
    fi
fi

