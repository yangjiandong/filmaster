import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.forum.models import Forum, Thread
from film20.threadedcomments.models import ThreadedComment

def upgrade_is_first_post():
    for thread in Thread.objects.all():
        comment = ThreadedComment.objects.filter(object_id=thread.id).order_by('date_submitted')[:1]
        print comment
        comment[0].is_first_post=True
        comment[0].save()
		#print comment[0].is_first_post

upgrade_is_first_post()