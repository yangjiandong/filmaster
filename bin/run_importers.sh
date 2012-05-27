#!/bin/bash
test1=`ps x | grep "run_import_ratings.py" | grep -v grep | awk '{ print $3 }' | wc -l`
test2=`ps x | grep "run_imdb_fetcher.py" | grep -v grep | awk '{ print $3 }' | wc -l`
if [ $test1 -eq 0 ]
then
    if [ $test2 -eq 0 ]
    then
        cd ~/filmaster-reloaded
        python ~/filmaster-reloaded/run_import_ratings.py
        python ~/filmaster-reloaded/run_imdb_fetcher.py -f > /dev/null 2>&1
    fi
else
    echo "import scripts running..."
fi
