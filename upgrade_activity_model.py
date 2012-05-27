import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from datetime import datetime

#from film20.blog.models import Post
from film20.core.models import ShortReview
from film20.core.models import Film
#from film20.threadedcomments.models import ThreadedComment
from film20.useractivity.models import UserActivity

class UpgradeActivity():

#    def upgrade_blog_activity(self):
#        
#        posts = Post.objects.all()
#        for post in posts:
#            activity = UserActivity(user = post.author.user, activity_type = UserActivity.TYPE_POST, created_at = post.created_at ,post = post)
#            activity.save()
#        
#    def upgrade_shortreview_activity(self):
#        
#        short_reviews = ShortReview.objects.all()
#        for short_review in short_reviews:
#            film = Film.objects.get(pk=short_review.object.pk)
#            activity = UserActivity(user = short_review.user, activity_type = UserActivity.TYPE_SHORT_REVIEW, short_review = short_review, film=film)
#            activity.save()
#        
#    def upgrade_comment_activity(self):
#        
#        comments = ThreadedComment.objects.all()
#        if comments:
#            for comment in comments:
#                activity = UserActivity(user = comment.user, activity_type = UserActivity.TYPE_COMMENT, created_at = comment.date_submitted, comment = comment)
#                activity.save()
    
    def find_missing_short_reviews(self):  
        short_reviews = ShortReview.objects.all()
        for short_review in short_reviews:
            try:
                activity = UserActivity.objects.get(activity_type = UserActivity.TYPE_SHORT_REVIEW, short_review = short_review)
            except UserActivity.DoesNotExist:
                film = Film.objects.get(pk=short_review.object.pk)
                activity = UserActivity(user = short_review.user, activity_type = UserActivity.TYPE_SHORT_REVIEW, short_review = short_review, film=film, created_at=short_review.created_at)
                activity.save()
    
def main():
    activity = UpgradeActivity()
    #activity.upgrade_blog_activity()
    #activity.upgrade_shortreview_activity()
    #activity.upgrade_comment_activity()
    activity.find_missing_short_reviews()

if __name__ == "__main__":
    main()
