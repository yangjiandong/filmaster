#!/bin/bash
cd /home/apps/filmasterpl/filmaster-stable
#NOW=$(date +"%y-%m-%d-%H-%M")
#echo $NOW
#python run_recom_new_users.sh
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
. run_compute_probable_scores2.sh
NOW=$(date +"%y-%m-%d-%H-%M")
echo $NOW
