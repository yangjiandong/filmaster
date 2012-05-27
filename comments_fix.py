import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from django.contrib.contenttypes.models import ContentType

def fix_comments():
    from film20.threadedcomments.models import ThreadedComment
    content_type_forum = ContentType.objects.get(app_label="forum", model="thread")

    for comment in ThreadedComment.objects.filter(is_first_post=False, content_type=content_type_forum):

        content_type = ContentType.objects.get(app_label="threadedcomments", model="comment")
        comment.content_type = content_type
fix_comments()
