#!/bin/bash
cd /home/filmaster/film20/fetcher/
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
LOGFILE="fetch.$NOW.log"
MOVIEFILE="movie_list.$NOW.txt"
python box_office_fetcher.py
python imdb_fetcher.py -c "http" -l
mv movie_list.txt list/$MOVIEFILE
mv fetch.log log/$LOGFILE
