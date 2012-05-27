#!/usr/bin/env python
import os
import subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import compute_film_comparators

compute_film_comparators()


