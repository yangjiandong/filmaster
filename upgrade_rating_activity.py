import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
import datetime
from film20.core.models import Rating
from film20.useractivity.models import UserActivity
from django.contrib.auth.models import User
import datetime

class RatingActivityUpgrade:
    def actor_rating_upgrade(self):
        users = User.objects.all()
        for user in users:
            ratings = Rating.objects.filter(user=user, type=3, last_rated__gte=datetime.datetime.now()-datetime.timedelta(hours=24)).exclude(rating__isnull = True)
            if len(ratings) != 0:
                rated_objects_html = ""
                for rating in ratings:
                    rated_object_html = "<a href=\"/osoba/" + rating.parent.permalink +"\">" + unicode(rating.actor) + " (" + str(rating.rating) + ")</a>,"
                    rated_objects_html = rated_objects_html + rated_object_html
                
                activity = UserActivity(user = user,
                                    activity_type = UserActivity.TYPE_RATING, 
                                    rate_type=UserActivity.TYPE_ACTOR,
                                    rated_objects_count=len(ratings),
                                    rated_objects_html=rated_objects_html)
                activity.save()
            
                for rating in ratings:
                    activity.rated_objects.add(rating)

    def director_rating_upgrade(self):
        users = User.objects.all()
        for user in users:
            ratings = Rating.objects.filter(user=user, type=2, last_rated__gte=datetime.datetime.now()-datetime.timedelta(hours=24)).exclude(rating__isnull = True)
            if len(ratings) != 0:
                rated_objects_html = ""
                for rating in ratings:
                    rated_object_html = "<a href=\"/osoba/" + rating.parent.permalink +"\">" + unicode(rating.director) + " (" + str(rating.rating) + ")</a>,"
                    rated_objects_html = rated_objects_html + rated_object_html

                activity = UserActivity(user = user, 
                                    activity_type = UserActivity.TYPE_RATING, 
                                    rate_type=UserActivity.TYPE_DIRECTOR,
                                    rated_objects_count=len(ratings),
                                    rated_objects_html=rated_objects_html)
                activity.save()
                for rating in ratings:
                    activity.rated_objects.add(rating)
                
                            
    def film_rating_upgrade(self):
        users = User.objects.all()
        for user in users:
            ratings = Rating.objects.filter(user=user, type=1, last_rated__gte=datetime.datetime.now()-datetime.timedelta(hours=24)).exclude(rating__isnull = True)
            if len(ratings) != 0:
                rated_objects_html = ""
                for rating in ratings:
                    rated_object_html = "<a href=\"/film/" + rating.parent.permalink +"\">" + unicode(rating.film) + " (" + str(rating.rating) + ")</a>,"
                    rated_objects_html = rated_objects_html + rated_object_html

                activity = UserActivity(user = user, 
                                    activity_type = UserActivity.TYPE_RATING, 
                                    rate_type=UserActivity.TYPE_FILM,
                                    rated_objects_count=len(ratings),
                                    rated_objects_html=rated_objects_html)
                activity.save()
                for rating in ratings:
                    activity.rated_objects.add(rating)
                
def main():
    activity = RatingActivityUpgrade()
    activity.film_rating_upgrade()
    activity.director_rating_upgrade()
    activity.actor_rating_upgrade()
if __name__ == "__main__":
    main()


