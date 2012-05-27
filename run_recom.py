#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import do_create_comparators 
from film20.core.rating_helper import *
from film20.core.models import *
 
do_create_comparators()

from film20.tagging.models import *

#Tag.objects.update_all_weights()

#from film20.recommendations.bot_helper import create_comparators_for_user
#user = User.objects.get(username='michukopenid')
#all_users = User.objects.all()
#create_comparators_for_user(user, all_users)
