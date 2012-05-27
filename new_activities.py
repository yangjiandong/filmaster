import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

def fix_notes():
    from film20.blog.models import Post
    for post in Post.objects.iterator():
        try:
            post.save_activity()
#            print post
        except Exception, e:
            print e

def fix_short_reviews():
    from film20.core.models import ShortReview
    for short in ShortReview.objects.iterator():
        try:
            short.save_activity()
#            print short
        except Exception, e:
            print e

def fix_externallinks():
    from film20.externallink.models import ExternalLink
    for link in ExternalLink.objects.iterator():
        try:
            link.save_activity()
#            print link
        except Exception, e:
            print e

def fix_comments():
    from film20.threadedcomments.models import ThreadedComment
    for comment in ThreadedComment.objects.iterator():
        try:
            comment.save_activity()
#            print comment
        except Exception, e:
            print e

def fix_followers():
    from film20.useractivity.models import UserActivity
    for act in UserActivity.objects.filter(activity_type=UserActivity.TYPE_FOLLOW).iterator():
        act.username = act.user.username
        act.save()

from django.contrib.contenttypes.models import ContentType

def fix_comments2():
    from film20.threadedcomments.models import ThreadedComment
    content_type = ContentType.objects.get(app_label="threadedcomments", model="threadedcomment")

    for comment in ThreadedComment.objects.filter(is_first_post=False, content_type=content_type):
        content_type_forum = ContentType.objects.get(app_label="forum", model="thread")
        
        comment.content_type = content_type_forum
        comment.save()

def fix_checkins():
    from film20.showtimes.models import ScreeningCheckIn
    for check in ScreeningCheckIn.objects.iterator():
        check.save_activity()

fix_comments2()
fix_notes()
fix_short_reviews()
fix_externallinks()
fix_comments()
fix_followers()
fix_checkins()
