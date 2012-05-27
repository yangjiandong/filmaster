from film20.utils.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.conf import settings
from film20.core.models import Film, Object, ShortReview, Rating, UserRatingTimeRange, RatingComparator
from film20.blog.models import Post
from film20.config.urls import *
from film20.useractivity.models import UserActivity
from film20.useractivity.useractivity_helper import PlanetTagHelper, UserActivityHelper
from film20.recommendations.recom_helper import RecomHelper
from film20.externallink.models import ExternalLink
from film20.threadedcomments.models import ThreadedComment
from film20.import_ratings.import_ratings_helper import save_rating
from film20.core import rating_helper

class UserActivityTestCase(TestCase):
    def setUp(self):
        Film.objects.filter(imdb_code__lt=1000).delete()

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()
        self.u2 = User(username='adz', email='b.orysmusielak@gmail.com')
        self.u2.save()
        self.u3 = User(username='turin', email='borysm.usielak@gmail.com')
        self.u3.save()
        self.u4 = User(username='olamus', email='borysmu.sielak@gmail.com')
        self.u4.save()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save()
        self.film.save_tags('comedy')

        self.film1 = Film()
        self.film1.title = "Battlefield Earth III"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "battlefirld-earth-iii"
        self.film1.release_year = 2010
        self.film1.save()
        self.film1.save_tags('sci-fi')

        self.film2 = Film()
        self.film2.title = "Battlefield Earth IV"
        self.film2.type = Object.TYPE_FILM
        self.film2.permalink = "battlefirld-earth-iv"
        self.film2.release_year = 2010
        self.film2.save()
        self.film2.save_tags('horror')

        rating_helper.rate(self.u1, 8, self.film.id)
        rating_helper.rate(self.u1, 8, self.film1.id)
        rating_helper.rate(self.u1, 8, self.film2.id)
        rating_helper.rate(self.u2, 8, self.film2.id, _skip_activity=True)

    def films_for_comparator(self):
        # films for comnparator
        self.f1 = Film(type=1, permalink='przypadek', imdb_code=111, status=1, version=1,
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f1.save()

        self.f2 = Film(type=1, permalink='wrestler', imdb_code=112, status=1, version=1,
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f2.save()

        self.f3 = Film(type=1, permalink='american-history-x', imdb_code=113, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f3.save()

        self.f4 = Film(type=1, permalink='the-big-lebowski', imdb_code=114, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f4.save()

        self.f5 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=115, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f5.save()

        self.f6 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=116, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f6.save()

        self.f7 = Film(type=1, permalink='the-alien', imdb_code=117, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f7.save()

        self.f8 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=118, status=1, version=1,
        release_year=1991, title='Terminator 2: Judgment Day', popularity=1, popularity_month=1)
        self.f8.save()

        self.f9 = Film(type=1, permalink='przypadek', imdb_code=119, status=1, version=1,
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f9.save()

        self.f10 = Film(type=1, permalink='wrestler', imdb_code=120, status=1, version=1,
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f10.save()

        self.f11 = Film(type=1, permalink='american-history-x', imdb_code=121, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f11.save()

        self.f12 = Film(type=1, permalink='the-big-lebowski', imdb_code=122, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f12.save()

        self.f13 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=123, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f13.save()

        self.f14 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=124, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f14.save()

        self.f15 = Film(type=1, permalink='the-alien', imdb_code=125, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f15.save()

        self.f16 = Film(type=1, permalink='przypadek', imdb_code=126, status=1, version=1,
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f16.save()

        self.f17 = Film(type=1, permalink='wrestler', imdb_code=127, status=1, version=1,
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f17.save()

        self.f18 = Film(type=1, permalink='american-history-x', imdb_code=128, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f18.save()

        self.f19 = Film(type=1, permalink='the-big-lebowski', imdb_code=129, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f19.save()

        self.f20 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=130, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f20.save()

        self.f21 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=131, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f21.save()

        self.f22 = Film(type=1, permalink='the-alien', imdb_code=132, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f22.save()

        self.f23 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=133, status=1, version=1,
        release_year=1991, title='Terminator 2: Judgment Day', popularity=1, popularity_month=1)
        self.f23.save()

        self.f24 = Film(type=1, permalink='przypadek', imdb_code=134, status=1, version=1,
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f24.save()

        self.f25 = Film(type=1, permalink='wrestler', imdb_code=135, status=1, version=1,
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f25.save()

        self.f26 = Film(type=1, permalink='american-history-x', imdb_code=136, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f26.save()

        self.f27 = Film(type=1, permalink='the-big-lebowski', imdb_code=137, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f27.save()

        self.f28 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=138, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f28.save()

        self.f29 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=139, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f29.save()

        self.f30 = Film(type=1, permalink='the-alien', imdb_code=140, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f30.save()

        self.f1.save_tags('comedy drama horror animation mystery')
        self.f2.save_tags('comedy sci-fi thriller series')
        self.f3.save_tags('comedy')
        self.f4.save_tags('sci-fi')
        self.f5.save_tags('horror')
        self.f6.save_tags('thriller')
        self.f7.save_tags('drama')
        self.f8.save_tags('series')
        self.f9.save_tags('sci-fi')
        self.f10.save_tags('fantasy')
        self.f11.save_tags('mystery')
        self.f12.save_tags('action')
        self.f13.save_tags('adventure')
        self.f14.save_tags('animation')
        self.f15.save_tags('family')
        self.f16.save_tags('thriller')
        self.f17.save_tags('drama')
        self.f18.save_tags('series')
        self.f19.save_tags('sci-fi')
        self.f20.save_tags('fantasy')
        self.f21.save_tags('comedy')
        self.f22.save_tags('animation')
        self.f23.save_tags('comedy')
        self.f24.save_tags('sci-fi')
        self.f25.save_tags('horror')
        self.f26.save_tags('thriller')
        self.f27.save_tags('drama')
        self.f28.save_tags('series')
        self.f29.save_tags('sci-fi')
        self.f30.save_tags('fantasy')

        #First user ratings
        save_rating(self.f1, self.u1, 1)
        save_rating(self.f2, self.u1, 2)
        save_rating(self.f3, self.u1, 3)
        save_rating(self.f4, self.u1, 4)
        save_rating(self.f5, self.u1, 5)
        save_rating(self.f6, self.u1, 6)
        save_rating(self.f7, self.u1, 7)
        save_rating(self.f8, self.u1, 8)
        save_rating(self.f9, self.u1, 9)
        save_rating(self.f10, self.u1, 10)
        save_rating(self.f11, self.u1, 1)
        save_rating(self.f12, self.u1, 2)
        save_rating(self.f13, self.u1, 3)
        save_rating(self.f14, self.u1, 4)
        save_rating(self.f15, self.u1, 5)
        save_rating(self.f16, self.u1, 6)
        save_rating(self.f17, self.u1, 7)
        save_rating(self.f18, self.u1, 8)
        save_rating(self.f19, self.u1, 9)
        save_rating(self.f20, self.u1, 10)
        save_rating(self.f21, self.u1, 1)
        save_rating(self.f22, self.u1, 2)
        save_rating(self.f23, self.u1, 3)
        save_rating(self.f24, self.u1, 4)
        save_rating(self.f25, self.u1, 5)
        save_rating(self.f26, self.u1, 6)
        save_rating(self.f27, self.u1, 7)
        save_rating(self.f28, self.u1, 8)
        save_rating(self.f29, self.u1, 9)
        save_rating(self.f30, self.u1, 10)

        #Second user ratings - more than minimal common films requirement (15)
        save_rating(self.f1, self.u2, 1)
        save_rating(self.f2, self.u2, 2)
        save_rating(self.f3, self.u2, 3)
        save_rating(self.f4, self.u2, 4)
        save_rating(self.f5, self.u2, 5)
        save_rating(self.f6, self.u2, 6)
        save_rating(self.f7, self.u2, 7)
        save_rating(self.f8, self.u2, 8)
        save_rating(self.f9, self.u2, 9)
        save_rating(self.f10, self.u2, 10)
        save_rating(self.f11, self.u2, 1)
        #save_rating(self.f12, self.u2, 2)
        save_rating(self.f13, self.u2, 3)
        #save_rating(self.f14, self.u2, 4)
        save_rating(self.f15, self.u2, 5)
        #save_rating(self.f16, self.u2, 6)
        save_rating(self.f17, self.u2, 7)
        #save_rating(self.f18, self.u2, 8)
        save_rating(self.f19, self.u2, 9)
        #save_rating(self.f20, self.u2, 10)
        save_rating(self.f21, self.u2, 1)
        #save_rating(self.f22, self.u2, 2)
        save_rating(self.f23, self.u2, 3)
        #save_rating(self.f24, self.u2, 4)
        save_rating(self.f25, self.u2, 5)
        #save_rating(self.f26, self.u2, 6)
        save_rating(self.f27, self.u2, 7)
        #save_rating(self.f28, self.u2, 8)
        save_rating(self.f29, self.u2, 9)
        #save_rating(self.f30, self.u2, 10)

        # Third user ratings - equal with minimal common films requirement (15)
        #save_rating(self.f1, self.u3, 1)
        #save_rating(self.f2, self.u3, 2)
        #save_rating(self.f3, self.u3, 3)
        #save_rating(self.f4, self.u3, 4)
        #save_rating(self.f5, self.u3, 5)
        #save_rating(self.f6, self.u3, 6)
        #save_rating(self.f7, self.u3, 7)
        #save_rating(self.f8, self.u3, 8)
        #save_rating(self.f9, self.u3, 9)
        #save_rating(self.f10, self.u3, 10)
        #save_rating(self.f11, self.u3, 1)
        #save_rating(self.f12, self.u3, 2)
        #save_rating(self.f13, self.u3, 3)
        #save_rating(self.f14, self.u3, 4)
        #save_rating(self.f15, self.u3, 5)
        save_rating(self.f16, self.u3, 6)
        save_rating(self.f17, self.u3, 7)
        save_rating(self.f18, self.u3, 8)
        save_rating(self.f19, self.u3, 9)
        save_rating(self.f20, self.u3, 10)
        save_rating(self.f21, self.u3, 1)
        save_rating(self.f22, self.u3, 2)
        save_rating(self.f23, self.u3, 3)
        save_rating(self.f24, self.u3, 4)
        save_rating(self.f25, self.u3, 5)
        save_rating(self.f26, self.u3, 6)
        save_rating(self.f27, self.u3, 7)
        save_rating(self.f28, self.u3, 8)
        save_rating(self.f29, self.u3, 9)
        save_rating(self.f30, self.u3, 10)

        # Fourth user ratings - less than minimal films requirement
        #save_rating(self.f1, self.u4, 1)
        #save_rating(self.f2, self.u4, 2)
        #save_rating(self.f3, self.u4, 3)
        #save_rating(self.f4, self.u4, 4)
        #save_rating(self.f5, self.u4, 5)
        #save_rating(self.f6, self.u4, 6)
        #save_rating(self.f7, self.u4, 7)
        #save_rating(self.f8, self.u4, 8)
        #save_rating(self.f9, self.u4, 9)
        #save_rating(self.f10, self.u4, 10)
        #save_rating(self.f11, self.u4, 1)
        #save_rating(self.f12, self.u4, 2)
        #save_rating(self.f13, self.u4, 3)
        #save_rating(self.f14, self.u4, 4)
        #save_rating(self.f15, self.u4, 5)
        #save_rating(self.f16, self.u4, 6)
        #save_rating(self.f17, self.u4, 7)
        #save_rating(self.f18, self.u4, 8)
        #save_rating(self.f19, self.u4, 9)
        #save_rating(self.f20, self.u4, 10)
        save_rating(self.f21, self.u4, 1)
        save_rating(self.f22, self.u4, 2)
        save_rating(self.f23, self.u4, 3)
        save_rating(self.f24, self.u4, 4)
        save_rating(self.f25, self.u4, 5)
        save_rating(self.f26, self.u4, 6)
        save_rating(self.f27, self.u4, 7)
        save_rating(self.f28, self.u4, 8)
        save_rating(self.f29, self.u4, 9)
        save_rating(self.f30, self.u4, 10)
        
    def clean_data(self):
        User.objects.all().delete()
        Post.objects.all().delete()
        Rating.objects.all().delete()
        UserActivity.objects.all().delete()

        
    def test_saving_post_activity(self):
        """
            Test saving post activity
        """
        self.initialize()

        # set up post
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        # this method will call save_activity method and in this case create new activity
        post.save()

        activity = UserActivity.objects.get(post=post)

        # testing if activity was saved properly
        self.failUnlessEqual(activity.title, post.title)
        self.failUnlessEqual(activity.content, post.body)
        self.failUnlessEqual(activity.permalink, post.get_absolute_url())
        self.failUnlessEqual(activity.status, post.status)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_POST)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film_title, self.film.title)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)

        # TODO: add a get_absolute_url(), get_slug() and get_subdomain() test

    def test_updating_post_activity(self):
        """
            Test updating post activity
        """
        self.initialize()

        # set up post
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        post.title = "Bum bum bum"
        post.permalink = "bum-bum-bum"
        post.body = "Lubuduubu lubu dubu niech zyje nam prezes naszego klubu!"
        post.status = Object.DRAFT_STATUS
        post.save()
        
        activity = UserActivity.objects.get(post=post)

        # testing if activity was updated properly
        self.failUnlessEqual(activity.title, "Bum bum bum")
        self.failUnlessEqual(activity.content, "Lubuduubu lubu dubu niech zyje nam prezes naszego klubu!")
        self.failUnlessEqual(activity.permalink, post.get_absolute_url())
        self.failUnlessEqual(activity.status, UserActivity.DRAFT_STATUS)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_POST)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film_title, self.film.title)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)

    def test_saving_shortreview_activity(self):
        """
           Test saving shortreview activity     
        """

        self.initialize()

        # set up Shortreview
        obj = Object.objects.get(id=self.film.id)
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.object = obj
        shortreview.kind = ShortReview.REVIEW
        shortreview.save()

        activity = UserActivity.objects.get(short_review=shortreview)

        # testing if activity was saved properly
        self.failUnlessEqual(activity.title, shortreview.get_title())
        self.failUnlessEqual(activity.content, shortreview.review_text)
        self.failUnlessEqual(activity.permalink, shortreview.get_absolute_url())
        self.failUnlessEqual(activity.status, shortreview.status)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_SHORT_REVIEW)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film_title, self.film.title)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)

    def test_updating_shortreview_activity(self):
        """
           Test updating shortreview activity
        """

        self.initialize()

        # set up Shortreview
        obj = Object.objects.get(id=self.film.id)
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.object = obj
        shortreview.kind = ShortReview.REVIEW
        shortreview.save()

        shortreview = ShortReview.objects.get(id=shortreview.id)
        shortreview.review_text = "Lorem ipsum"
        shortreview.status = Object.DELETED_STATUS
        shortreview.save()

        activity = UserActivity.objects.get(short_review=shortreview)
        
        # testing if activity was updated properly
        self.failUnlessEqual(activity.title, shortreview.get_title())
        self.failUnlessEqual(activity.content, "Lorem ipsum")
        self.failUnlessEqual(activity.permalink, shortreview.get_absolute_url())
        self.failUnlessEqual(activity.status, UserActivity.DELETED_STATUS)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_SHORT_REVIEW)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film_title, self.film.title)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)

    def test_saving_externallink_activity(self):
        """
            Test saving externallink activity
        """

        self.initialize()

        # set up Externallink

        ext = ExternalLink()
        ext.title = "Link title!"
        ext.url = "http://filmaster.pl"
        ext.url_kind = ExternalLink.REVIEW
        ext.excerpt = "Lorem ipsum"
        ext.film = self.film
        ext.user = self.u1
        ext.status = Object.PUBLIC_STATUS
        ext.type = Object.TYPE_LINK
        ext.save()

        self.assertRaises(UserActivity.DoesNotExist, UserActivity.objects.get, link=ext)
        
        ext.moderation_status = ExternalLink.STATUS_ACCEPTED
        ext.save()

        activity = UserActivity.objects.get(link=ext)

        # testing if activity was saved properly
        self.failUnlessEqual(activity.title, ext.title)
        self.failUnlessEqual(activity.content, ext.excerpt)
        self.failUnlessEqual(activity.get_absolute_url(), ext.get_absolute_url())
        self.failUnlessEqual(activity.status, ext.status)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_LINK)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film_title, self.film.title)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)

    def test_updating_externallink_activity(self):
        """
            Test updating externallink activity
        """

        self.initialize()

        # set up Externallink

        ext = ExternalLink()
        ext.title = "Link title!"
        ext.url = "http://filmaster.pl"
        ext.url_kind = ExternalLink.REVIEW
        ext.excerpt = "Lorem ipsum"
        ext.film = self.film
        ext.user = self.u1
        ext.status = Object.PUBLIC_STATUS
        ext.type = Object.TYPE_LINK
        ext.save()

        ext.url = "http://osnews.pl"
        ext.excerpt = "Lorem lorem"
        ext.save()

        activity = UserActivity.objects.get(link=ext)

        # testing if activity was saved properly
        self.failUnlessEqual(activity.title, ext.title)
        self.failUnlessEqual(activity.content, "Lorem lorem")
        self.failUnlessEqual(activity.get_absolute_url(), ext.get_absolute_url())
        self.failUnlessEqual(activity.status, ext.status)
        self.failUnlessEqual(activity.url, "http://osnews.pl")
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_LINK)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film_title, self.film.title)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)

    def test_saving_comment_activity(self):
        """
            Test saving comment activity
        """
        self.initialize()

        # set up post for commenting
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        comment = ThreadedComment()
        comment.user = self.u1
        comment.comment = "Lorem ipsum"
        comment.content_object = post
        comment.status = Object.PUBLIC_STATUS
        comment.type=Object.TYPE_COMMENT
        comment.permalink="COMMENT"
        comment.save()

        activity = UserActivity.objects.get(comment=comment)

        # testing if activity was saved properly
        self.failUnlessEqual(activity.title, comment.content_object.get_comment_title())
        self.failUnlessEqual(activity.content, comment.comment)
        if settings.ENSURE_OLD_STYLE_PERMALINKS:
            self.failUnlessEqual(activity.permalink, comment.content_object.get_absolute_url_old_style()+"#"+ str(comment.id))
        else:
            self.failUnlessEqual(activity.permalink, comment.content_object.get_absolute_url()+"#"+ str(comment.id))
        self.failUnlessEqual(activity.status, comment.status)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_COMMENT)
        self.failUnlessEqual(activity.username, self.u1.username)

        #planet_tag_helper without tag = 1 comment
        pth = PlanetTagHelper()
        comments = pth.planet_tag_comments()
        self.assertEquals(len(comments), 1)
        
        #planet_tag_helper with tag 'comedy' = 0 comment
        #no assigned films to comment
        pth_tags = PlanetTagHelper(tag='comedy')
        comments = pth_tags.planet_tag_comments()
        self.assertEquals(len(comments), 0)

    def test_updating_comment_activity(self):
        """
            Test updating comment activity
        """

        self.initialize()

        # set up post for commenting
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        comment = ThreadedComment()
        comment.user = self.u1
        comment.comment = "Lorem ipsum"
        comment.content_object = post
        comment.status = Object.PUBLIC_STATUS
        comment.type=Object.TYPE_COMMENT
        comment.permalink="COMMENT"
        comment.save()

        comment.comment = "siala lala tralala"
        comment.status = Object.DELETED_STATUS
        comment.save()
        activity = UserActivity.objects.get(comment=comment)

        # testing if activity was updated properly
        self.failUnlessEqual(activity.title, comment.content_object.get_comment_title())
        self.failUnlessEqual(activity.content, "siala lala tralala")
        if settings.ENSURE_OLD_STYLE_PERMALINKS:
            self.failUnlessEqual(activity.permalink, comment.content_object.get_absolute_url_old_style()+"#"+ str(comment.id))
        else:
            self.failUnlessEqual(activity.permalink, comment.content_object.get_absolute_url()+"#"+ str(comment.id))
        self.failUnlessEqual(activity.status, UserActivity.DELETED_STATUS)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_COMMENT)
        self.failUnlessEqual(activity.username, self.u1.username)

    def test_saving_draft_post_activity(self):
        """
           Test saving draft activity
           Make sure that activity is not created for draft posts
        """

        self.initialize()
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.DRAFT_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        post_activities = UserActivity.objects.filter(activity_type=UserActivity.TYPE_POST)

        self.failUnlessEqual(post_activities.count(), 1) # now we want to create an activity each time
        act = UserActivity.objects.get(post=post)
        self.failUnlessEqual(act.status, UserActivity.DRAFT_STATUS)

        post.status = Post.PUBLIC_STATUS
        post.save()
        self.failUnlessEqual(post_activities.count(), 1)
        act = UserActivity.objects.get(post=post)
        self.failUnlessEqual(act.status, UserActivity.PUBLIC_STATUS)

        post.status = Post.DRAFT_STATUS
        post.save()
        self.failUnlessEqual(post_activities.count(), 1)
        act = UserActivity.objects.get(post=post)
        self.failUnlessEqual(act.status, UserActivity.DRAFT_STATUS)

    def test_deleting_post_activity(self):
        """
            Test deleting post activity
        """

        self.initialize()
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        act = UserActivity.objects.get(post=post)

        self.failUnlessEqual(act.status, UserActivity.PUBLIC_STATUS)

        post.status = Object.DELETED_STATUS
        post.save()

        act = UserActivity.objects.get(post=post)
        self.failUnlessEqual(act.status, UserActivity.DELETED_STATUS)

    def test_updating_relatedfilm_post_activity(self):
        """
            Test updating film fields in post activity when related films
            are removed from post
        """
        self.initialize()
        self.client.login(username='michuk', password='secret')
        
        # set up post
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        activity = UserActivity.objects.get(post=post)

        # testing if activity was saved properly
        self.failUnlessEqual(activity.title, "Lorem ipsum")
        self.failUnlessEqual(activity.content, "siala lala tralala")
        self.failUnlessEqual(activity.permalink, post.get_absolute_url())
        self.failUnlessEqual(activity.status, UserActivity.PUBLIC_STATUS)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_POST)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film is None, False)
        self.failUnlessEqual(activity.film_permalink, self.film.permalink)
        self.failUnlessEqual(activity.film_title, self.film.title)

        # update post
        post.title = "New title"
        post.body = "Lorem ipsum! Lorem ipsum! Lorem ipsum!"
        post.related_film = []
        post.save()
        activity = UserActivity.objects.get(post=post)

        # testing if activity was updated properly
        self.failUnlessEqual(activity.title, "New title")
        self.failUnlessEqual(activity.content, "Lorem ipsum! Lorem ipsum! Lorem ipsum!")
        self.failUnlessEqual(activity.permalink, post.get_absolute_url())
        self.failUnlessEqual(activity.status, UserActivity.PUBLIC_STATUS)
        self.failUnlessEqual(activity.activity_type, UserActivity.TYPE_POST)
        self.failUnlessEqual(activity.username, self.u1.username)
        self.failUnlessEqual(activity.film is None, True)
        self.failUnlessEqual(activity.film_permalink, None)
        self.failUnlessEqual(activity.film_title, None)

    def test_rating_activity(self):
        """
           Test creating rating activity     
        """

        self.initialize()

        ratings = Rating.objects.filter(user=self.u1)

        ua = UserActivity.objects.filter(activity_type=UserActivity.TYPE_RATING, user=self.u1)
        self.assertEquals(len(ua), 3)

    def test_planet_tag(self):
        # --- Initialize ---
        self.initialize()
        helper_without_tags = PlanetTagHelper()
        helper_with_tags = PlanetTagHelper(tag='comedy')
        recom_helper = RecomHelper()
        user_activity_helper = UserActivityHelper()

        # --- setup followers ---
        self.u1.followers.follow(self.u2)
        self.u1.followers.follow(self.u3)
        self.u1.followers.follow(self.u4)

        # similar users
        from film20.recommendations.bot_helper import do_create_comparators
        self.films_for_comparator()
        do_create_comparators()

        friends_list = recom_helper.get_following_ids_as_list(self.u1)
        friends_without_activities = helper_without_tags.planet_tag_friends(friends_list)
        self.assertEquals(len(friends_without_activities), 0)
        
        similar_users_list = user_activity_helper.get_similar_users_list(request)
        similar_users_without_tags = helper_without_tags.planet_tag_similar_users(similar_users_list)
        self.assertEquals(len(similar_users_without_tags), 0)

        notes_without_tags = helper_without_tags.planet_tag_notes()
        self.assertEquals(len(notes_without_tags), 0)

        all_planet_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_planet_activities), 0)

        # --- setup User activities ---
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()
        
        all_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_activities), 1)
        
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film1)
        post.save()
        
        all_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_activities), 2)
                
        obj = Object.objects.get(id=self.film2.id)
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.object = obj
        shortreview.kind = ShortReview.REVIEW
        shortreview.save()

        all_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_activities), 3)
        
        # Activities with 'comedy' tag
        all_activities_with_tags = helper_with_tags.planet_tag_all()
        self.assertEquals(len(all_activities_with_tags), 1)

        # --- setup followers activities ---
        post = Post()
        post.title = "#1 Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u2
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        post.save()

        all_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_activities), 4)

        post = Post()
        post.title = "#2 Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u3
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film1)
        post.save()

        all_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_activities), 5)

        obj = Object.objects.get(id=self.film2.id)
        shortreview = ShortReview()
        shortreview.user = self.u4
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.object = obj
        shortreview.kind = ShortReview.REVIEW
        shortreview.save()

        all_activities = helper_without_tags.planet_tag_all()
        self.assertEquals(len(all_activities), 6)

        activities_with_tags = helper_with_tags.planet_tag_all()
        self.assertEquals(len(activities_with_tags), 2)

        all_friends_activities = helper_without_tags.planet_tag_friends(friends_list)
        self.assertEquals(len(all_friends_activities), 3)
        friends_activities_with_tag = helper_with_tags.planet_tag_friends(friends_list)
        self.assertEquals(len(friends_activities_with_tag), 1)

        # --- Check notes ---
        all_planet_notes = helper_without_tags.planet_tag_notes()
        self.assertEquals(len(all_planet_notes), 4)

        # Post notes with 'comedy' tag
        notes_activities_with_tag = helper_with_tags.planet_tag_notes()
        self.assertEquals(len(notes_activities_with_tag), 2)

        similar_users_activities = helper_without_tags.planet_tag_similar_users(similar_users_list)
        self.assertEquals(len(similar_users_activities), 2)

        users_with_tags = helper_with_tags.planet_tag_similar_users(similar_users_list)
        self.assertEquals(len(users_with_tags), 1)
        
        activities = UserActivity.objects.all() 
