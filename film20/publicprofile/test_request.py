# Django
from django.contrib.auth.models import User
from film20.utils.test import TestCase

# Project
from film20.core.models import ShortReview, Profile
from film20.useractivity.models import UserActivity
from film20.blog.models import Post
from film20.config import urls

class RequestTestCase(TestCase):
        
    def setUp(self):
        User.objects.all().delete()
        ShortReview.objects.all().delete()
        UserActivity.objects.all().delete()
        Profile.objects.all().delete()
        
        self.filmaster = User.objects.create_user('filmaster',
                                           'filmaster@filmaster.com',
                                           'secret')
        self.u1 = User.objects.create_user('michuk',
                                           'borys.musielak@gmail.com',
                                           'secret')

    def tearDown(self):
        User.objects.all().delete()
        ShortReview.objects.all().delete()
        UserActivity.objects.all().delete()
        Profile.objects.all().delete()

    def test_show_article_ok(self):
        """
            Test show_article - article exist!
        """
        
        ua = UserActivity()
        ua.activity_type = UserActivity.TYPE_POST
        ua.status = UserActivity.PUBLIC_STATUS
        ua.title = "Lorem ipsum"
        ua.content = "lalala"
        ua.user = self.u1
        ua.username = self.u1.username
        ua.post = Post()
        ua.post.title = ua.title
        ua.post.user = self.u1
        ua.post.body = ua.content
        ua.post.permalink = 'testowy-artykul'
        ua.post.save()

        ua.save()

        response = self.client.get(
            ua.get_absolute_url()
        )
        print ua.get_absolute_url()
        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(response.context['activity'].content, "lalala")

    def test_show_article_fail(self):
        """
            Test show_article - article does not exist
        """
        path = "/"+urls.urls["SHOW_PROFILE"]+"/rambo/"+urls.urls["ARTICLE"]+"/testowy-artykul/"
        response = self.client.get(
            path
        )
        self.failUnlessEqual(response.status_code, 404)

    def test_show_wall_post_ok(self):
        """
            Test show_wall_post - article exist!
        """
        shortreview = ShortReview()
        shortreview.user = self.u1
        shortreview.review_text = "sialala bumcyk cyk"
        shortreview.status = ShortReview.PUBLIC_STATUS
        shortreview.type = ShortReview.TYPE_SHORT_REVIEW
        shortreview.kind = ShortReview.REVIEW
        shortreview.save()

        response = self.client.get(
           shortreview.get_absolute_url()
        )

        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(response.context['activity'].content, "sialala bumcyk cyk")

    def test_show_wall_post_fail(self):
        """
            Test show_article - article does not exist
        """
        path = "/" + urls.urls["SHOW_PROFILE"] + "/rambo/" + urls.urls["WALL"] + "/1010101010101010101/"
        response = self.client.get(
            path
        )
        
        self.failUnlessEqual(response.status_code, 404)

    def test_show_public_profile(self):
        """
            Test show_public_profile view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/michuk/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 200)

    def test_show_public_profile_fail(self):
        """
            Test show_public_profile view - user does not exist
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/aabbcc/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 404)

    def test_show_followed(self):
        """
            Test show_followed view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/michuk/'+urls.urls['FOLLOWED']+'/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 200)

    def test_show_followed_fail(self):
        """
            Test show_followed view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/rambobo/'+urls.urls['FOLLOWED']+'/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 404)

    def test_show_followers(self):
        """
            Test show_followed view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/michuk/'+urls.urls['FOLLOWERS']+'/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 200)

    def test_show_followers_fail(self):
        """
            Test show_followed view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/rambobo/'+urls.urls['FOLLOWERS']+'/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 404)

    def test_show_collection(self):
        """
            Test show_collection view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/michuk/'+urls.urls['OWNED']+'/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 200)

    def test_show_rated_films(self):
        """
            Test show_rated_films view
        """
        path = '/'+urls.urls['SHOW_PROFILE']+'/michuk/'+urls.urls['RATED_FILMS']+'/'
        response = self.client.get(
            path
        )

        self.failUnlessEqual(response.status_code, 200)
