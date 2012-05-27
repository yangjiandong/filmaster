#!/usr/bin/env python
import os,sys
sys.path.append('/home/filmaster/filmaster-stable/fetcher')
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from django.contrib.sitemaps import ping_google
ping_google()
