import os
import re

os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.externallink.models import *
from django.db.models import Q

def fix_trailers():
    trailers = ExternalLink.objects.filter(Q(url_kind=ExternalLink.VIDEO)|\
                                           Q(url_kind=ExternalLink.TRAILER)|\
                                           Q(url_kind=ExternalLink.FULL_FEATURE)|\
                                           Q(url_kind=ExternalLink.OTHER_VIDEO))
    for trailer in trailers:
        pattern =  r"[\\?&]v=([^&#]*)"
        a = re.search(pattern, trailer.url)
        if a is not None:
            video_id = a.group(1)
            trailer.video_thumb = "http://img.youtube.com/vi/"+video_id+"/2.jpg"
            trailer.save()

def main():
    fix_trailers()

if __name__ == "__main__":
    main()