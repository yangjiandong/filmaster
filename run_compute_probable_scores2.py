#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from django.conf import settings
from film20.recommendations.bot_helper import do_compute_probable_scores, prepare_data, send_recommendations_calculated_notices

# only last day 
#do_compute_probable_scores()
# all time

params = dict(
    SQL_FILE = "temp_data/data_update.sql",
    DATABASE_PASSWORD = settings.DATABASES['default']['PASSWORD'],
    DATABASE_NAME = settings.DATABASES['default']['NAME'],
    DATABASE_HOST = settings.DATABASES['default']['HOST'],
    DATABASE_USER = settings.DATABASES['default']['USER'],
)

pre_cmds = """\
mkdir temp_data;
g++ count_recommendations.cpp -ocount_recommendations -O2;
"""

post_cmds = """\
./count_recommendations;
source /usr/local/bin/pg-env.sh 8.4
export PGPASSWORD=%(DATABASE_PASSWORD)s;
psql "%(DATABASE_NAME)s" -h "%(DATABASE_HOST)s" -U "%(DATABASE_USER)s" -f "%(SQL_FILE)s";
rm -r temp_data;
""" % params

os.system(pre_cmds)
prepare_data(False)
os.system(post_cmds)

send_recommendations_calculated_notices()
