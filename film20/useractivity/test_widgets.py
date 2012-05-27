from django.contrib.auth.models import User
from film20.utils.test import TestCase

from film20.core.models import Film, Object, ShortReview
from film20.useractivity.models import UserActivity
from film20.useractivity.templatetags.widgets import *

class WidgetsTest(TestCase):

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        # set up film
        self.film = Film()
        self.film.id = 233
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save(saved_by=2)
        self.film.save_tags("tag1", LANG="pl", saved_by=2)

        # set up film
        self.film1 = Film()
        self.film1.id = 236
        self.film1.title = "Battlefield Earth III"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "battlefirld-earth-iii"
        self.film1.release_year = 2011
        self.film1.save(saved_by=2)
        self.film1.save_tags("tag2", LANG="pl", saved_by=2)

        # set up activities
        sr = UserActivity(user=self.u1, film=self.film, object=self.film,
                content="Lorem", activity_type=UserActivity.TYPE_SHORT_REVIEW,
                featured=True)
        sr.save()

        sr1 = UserActivity()
        sr1.user = self.u1
        sr1.film = self.film1
        sr1.object = self.film1
        sr1.content = "ipsum"
        sr1.activity_type = UserActivity.TYPE_SHORT_REVIEW
        sr1.featured = True
        sr1.save()

        rating1 = UserActivity()
        rating1.activity_type = UserActivity.TYPE_RATING
        rating1.user = self.u1
        rating1.object = self.film
        rating1.featured = True
        rating1.save()

        rating2 = UserActivity()
        rating2.activity_type = UserActivity.TYPE_RATING
        rating2.user = self.u1
        rating2.object = self.film
        rating2.featured = True
        rating2.save()

    def clean_data(self):
        UserActivity.objects.all().delete()
        User.objects.all().delete()
        Film.objects.all().delete()


    def test_main_page_activity_list(self):
        """
            Test activity list for main page
        """

        self.initialize()
        activities = main_page_activity_list()['activities']
        is_rating = False
        is_short_review = False
        for act in activities:
            if act.activity_type == UserActivity.TYPE_RATING:
                is_rating = True
            if act.activity_type == UserActivity.TYPE_SHORT_REVIEW:
                is_short_review = True

        self.failUnlessEqual(is_rating, True)
        self.failUnlessEqual(is_short_review, True)

    def test_latest_checkins(self):
        """
            Test latest_checkins widget
        """

        # create 10 checkins activites
        self.initialize()
        
        for x in xrange(0, 10):
            act = UserActivity()
            act.activity_type = UserActivity.TYPE_CHECKIN
            act.user = self.u1
            act.save()

        act = latest_checkins()
        act = act['activities']
        self.failUnlessEqual(len(act), 4)

    def test_latest_ratings(self):
        """
            Test latest ratings widget      
        """
        self.initialize()

        act = latest_ratings()

        act = act['activities']

        self.failUnlessEqual(len(act), 2)
