#!/usr/bin/env/python

#select user_id,film_id,rating,guess_rating_alg1 from core_rating  where rating IS NOT NULL AND guess_rating_alg1 IS NOT NULL AND user_id=3
from django.db.models import Q

from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Rating
from film20.core.models import RatingComparator
from film20.core.models import FilmRanking
from django.contrib.auth.models import User
from django.db import connection, models

from decimal import *
from datetime import datetime
from datetime import date
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)
from math import sqrt

# count root mean squared error
def count_rmse(rows):
	S=0
	n=0
	for row in rows:
		S += (row[0]-row[1])**2
		n += 1
	return sqrt(S/n)
	print "Counted for", n, "ratings"



def do_test():
	query1="select rating,guess_rating_alg1 from core_rating  where rating IS NOT NULL AND guess_rating_alg1 IS NOT NULL"
	query2="select rat.rating AS rating,rec.guess_rating_alg2 as guess_rating_alg2 from core_rating rat LEFT JOIN core_recommendation rec ON rec.film_id=rat.film_id AND rec.user_id=rat.user_id AND rat.type=1 where rat.rating IS NOT NULL AND rec.guess_rating_alg2 IS NOT NULL"
	cursor = connection.cursor()
	cursor.execute(query1)
	print "RMSE for alg1:", count_rmse(cursor.fetchall())
	cursor.execute(query2)
	print "RMSE for alg2:", count_rmse(cursor.fetchall())
	cursor.close()
	#help(cursor)
