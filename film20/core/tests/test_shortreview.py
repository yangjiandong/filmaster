from film20.utils.test import TestCase
from django.contrib.auth.models import User
from film20.core.models import Film, Object, ShortReview, Rating
from film20.blog.models import Post
from film20.config.urls import *
from film20.useractivity.models import UserActivity
from django.conf import settings

class ShortReviewTestCase(TestCase):

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save()

        # set up rating
        self.rating = Rating()
        self.rating.parent = self.film
        self.rating.user = self.u1
        self.rating.film = self.film
        self.rating.type = Rating.TYPE_FILM
        self.rating.rating = 8
        self.rating.normalized = 8
        self.rating.save()


    def clean_data(self):
        User.objects.all().delete()
        Post.objects.all().delete()
        ShortReview.objects.all().delete()


    def test_saving_single_shortreview(self):
        """
           Test saving single shortreview
        """

        self.initialize()

        # set up Shortreview
        obj = Object.objects.get(id=self.film.id)
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.kind = ShortReview.REVIEW
        shortreview.object = obj
        shortreview.rating = self.rating
        shortreview.save()

        # testing if shortreview was saved
        sr = ShortReview.objects.get(object=obj)
        
        self.failUnlessEqual(sr.user, shortreview.user)
        self.failUnlessEqual(sr.review_text, "sialala bumcyk cyk")
        self.failUnlessEqual(sr.status, Object.PUBLIC_STATUS)
        self.failUnlessEqual(sr.type, Object.TYPE_SHORT_REVIEW)
        self.failUnlessEqual(sr.kind, ShortReview.REVIEW)
        self.failUnlessEqual(sr.rating.rating, 8)
        self.failUnlessEqual(sr.object, obj)


    def test_delete_single_shortreview(self):
        """
            Test deleting single shortreview
        """

        self.initialize()

        # set up Shortreview
        obj = Object.objects.get(id=self.film.id)
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.kind = ShortReview.REVIEW
        shortreview.object = obj
        shortreview.save()

        # there should be one short review
        self.failUnlessEqual(ShortReview.objects.all().count(), 1)

        sr = ShortReview.objects.get(object=obj)

        # deleting shortreview
        sr.delete()

        # there should be zero short reviews
        self.failUnlessEqual(ShortReview.objects.all().count(), 0)


    def test_edit_single_shortreview(self):
        """
            Test editing single shortreview
        """

        self.initialize()

        # set up Shortreview
        obj = Object.objects.get(id=self.film.id)
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = Object.PUBLIC_STATUS
        shortreview.type = Object.TYPE_SHORT_REVIEW
        shortreview.kind = ShortReview.REVIEW
        shortreview.object = obj
        shortreview.save()
        shortreview.rating.rating = 10
        shortreview.rating.save()

        # testing if shortreview was saved
        sr = ShortReview.objects.get(object=obj)

        self.failUnlessEqual(sr.review_text, "sialala bumcyk cyk")

        sr.review_text = "Lorem ipsum"
        sr.save()

        # testing if short review was edited successfully
        sr = ShortReview.objects.get(object=obj)
        self.failUnlessEqual(sr.review_text, "Lorem ipsum")
        self.failUnlessEqual(sr.rating.rating, 10)


    def test_saving_double_shortreviews(self):
        """
           Test saving two shortreviews about the same movie by the same user
        """

        self.initialize()

        # set up Shortreviews
        obj = Object.objects.get(id=self.film.id)
        shortreview1 = ShortReview()
        shortreview1.user = self.u1
        shortreview1.review_text = "sialala bumcyk cyk"
        shortreview1.status = Object.PUBLIC_STATUS
        shortreview1.type = Object.TYPE_SHORT_REVIEW
        shortreview1.kind = ShortReview.REVIEW
        shortreview1.object = obj
        shortreview1.rating = self.rating
        shortreview1.save()

        obj = Object.objects.get(id=self.film.id)
        shortreview2 = ShortReview()
        shortreview2.user = self.u1
        shortreview2.review_text = "Lorem ipsum lorem ipsum"
        shortreview2.status = Object.PUBLIC_STATUS
        shortreview2.type = Object.TYPE_SHORT_REVIEW
        shortreview2.kind = ShortReview.REVIEW
        shortreview2.object = obj
        shortreview2.rating = self.rating
        shortreview2.save()


        # testing if shortreview was saved
        sr = ShortReview.objects.filter(object=obj).order_by("created_at")

        self.failUnlessEqual(sr[0].user, shortreview1.user)
        self.failUnlessEqual(sr[0].review_text, "sialala bumcyk cyk")
        self.failUnlessEqual(sr[0].status, Object.PUBLIC_STATUS)
        self.failUnlessEqual(sr[0].type, Object.TYPE_SHORT_REVIEW)
        self.failUnlessEqual(sr[0].kind, ShortReview.REVIEW)
        self.failUnlessEqual(sr[0].rating.rating, 8)
        self.failUnlessEqual(sr[0].object, obj)

        self.failUnlessEqual(sr[1].user, shortreview1.user)
        self.failUnlessEqual(sr[1].review_text, "Lorem ipsum lorem ipsum")
        self.failUnlessEqual(sr[1].status, Object.PUBLIC_STATUS)
        self.failUnlessEqual(sr[1].type, Object.TYPE_SHORT_REVIEW)
        self.failUnlessEqual(sr[1].kind, ShortReview.REVIEW)
        self.failUnlessEqual(sr[1].rating.rating, 8)
        self.failUnlessEqual(sr[1].object, obj)


    def test_saving_wall_post(self):
        """
            Test saving wall post
        """

        self.initialize()

        wallpost = ShortReview()
        wallpost.user = self.u1
        wallpost.review_text = "sialala bumcyk cyk"
        wallpost.status = Object.PUBLIC_STATUS
        wallpost.kind = ShortReview.WALLPOST
        wallpost.type = Object.TYPE_SHORT_REVIEW
        wallpost.save()

        permalink = 'http://%s.%s/%s/%s/' % (self.u1.username, settings.DOMAIN, urls['WALL'], wallpost.id)
        wp = ShortReview.objects.all()[0]

        self.failUnlessEqual(wp.get_absolute_url(), permalink)
        self.failUnlessEqual(wp.user, wallpost.user)
        self.failUnlessEqual(wp.review_text, "sialala bumcyk cyk")
        self.failUnlessEqual(wp.status, Object.PUBLIC_STATUS)
        self.failUnlessEqual(wp.type, Object.TYPE_SHORT_REVIEW)
