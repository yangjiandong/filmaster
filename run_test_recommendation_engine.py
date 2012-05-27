#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.test_recom import do_test

# only last day 
#do_compute_probable_scores()
# all time
#do_compute_probable_scores(False)
do_test()

#from django.contrib.auth.models import User
#from film20.core.models import Film
#from film20.recommendations.bot_helper import compute_probable_scores_for_user, get_films_for_computing_scores

#user = User.objects.get(username='mamut')    
#films = get_films_for_computing_scores(False)
#compute_probable_scores_for_user(user, films)
