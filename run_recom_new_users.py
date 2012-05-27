#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import do_create_comparators 
from film20.core.rating_helper import *
from film20.core.models import *
 
do_create_comparators(True)

