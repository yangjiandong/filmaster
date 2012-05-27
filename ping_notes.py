import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.blog.models import PingbackNote
from film20.pingback.client import ping_dirs

import logging

def ping_notes():

    notes = PingbackNote.objects.select_related().filter(is_ping=False)

    for note in notes:
        logging.debug("Pinging note %s" % note.note)
        ping_dirs(note.note)
        note.is_ping = True
        note.save()

ping_notes()
