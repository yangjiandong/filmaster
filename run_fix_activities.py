#!/usr/bin/env python
import os
import subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import fix_film_ids_for_activities

fix_film_ids_for_activities()
