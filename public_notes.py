import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.blog.models import *

def public_notes():
    for note in Post.objects.iterator():
        if note.status == Post.PUBLIC_STATUS:
            note.is_public = True
            note.save()
public_notes()