#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import do_compute_probable_scores

# only last day, new users
do_compute_probable_scores(only_new_users=True)
