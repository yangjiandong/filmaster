#!/usr/bin/env python
import os, sys, getopt, glob, re
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import do_compute_probable_scores

from django.contrib.auth.models import User
from film20.core.models import Film
from film20.recommendations.bot_helper import compute_probable_scores_for_user, get_films_for_computing_scores

def main(argv = None):
    if argv is None:
        args = sys.argv[1:]

    username = args[0]
        
    if username==None:
        print "Enter user name as a parameter!"
    else:
        print "Computing scores for user: " + username
        user = User.objects.get(username=username)   
        compute_probable_scores_for_user(user)

if __name__ == "__main__":
    main()
