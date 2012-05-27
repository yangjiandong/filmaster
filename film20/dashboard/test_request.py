from django.contrib.auth.models import User
from film20.utils.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from film20.core.models import ShortReview
from film20.blog.models import Post
from film20.useractivity.models import UserActivity
from film20.config.urls import *

class RequestTestCase(TestCase):

    def initialize(self):
        self.clean_data()

        self.u1 = User.objects.create_user('michuk',
                                           'borys.musielak@gmail.com',
                                           'secret')
        self.u1.save()

    def clean_data(self):
        User.objects.all().delete()
        ShortReview.objects.all().delete()
        UserActivity.objects.all().delete()
        Post.objects.all().delete()

    def test_get_request(self):
        """
            Test get request for logged in user
        """
        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        response = self.client.get(reverse('show_dashboard'))
        self.failUnlessEqual(response.status_code, 200)

    def test_post_request(self):
        """
           Test post reqest for logged in user
        """
        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        data = {
            'text': "Lorem ipsum",
        }

        response = self.client.post(
                        reverse('show_dashboard'),
                        data,
                   )

        self.failUnlessEqual(response.status_code, 200)

        # chcecking if ShortReview with wall post kind was created
        sr = ShortReview.objects.get(user=self.u1)
        self.failUnlessEqual(sr.review_text, "Lorem ipsum")
        self.failUnlessEqual(sr.kind, ShortReview.WALLPOST)

        # chcecking if activity was created
        ua = UserActivity.objects.get(user=self.u1)
        self.failUnlessEqual(ua.content, "Lorem ipsum")

    def test_post_empty_form(self):
        """
            Test post request with empty form
        """
        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        data = {
            'text': "",
        }

        response = self.client.post(
                        reverse('show_dashboard'),
                        data,
                   )

        # empty form no activity is created!
        self.failUnlessEqual(UserActivity.objects.all().count(), 0)

    def test_my_articles(self):
        """
           Test my_articles view 
        """
        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Post.PUBLIC_STATUS
        post.type = Post.TYPE_POST
        post.save()

        post1 = Post()
        post1.title = "Lorem ipsum2"
        post1.permalink = "lorem-ipsum"
        post1.body = "siala lala tralala"
        post1.user = self.u1
        post1.status = Post.DRAFT_STATUS
        post1.type = Post.TYPE_POST
        post1.save()

        response = self.client.get("/"+urls["ARTICLES"]+"/")
        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)

    def test_show_wall_post_ok(self):
        """
            Test show_wall_post - article exist!
        """
        self.initialize()
        
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
        self.initialize()

        response = self.client.get(
            "/profil/rambo/wall/1010101010101010101/"
        )
        self.failUnlessEqual(response.status_code, 404)

    def test_save_new_article(self):
        """
            Test saving new article
        """
        self.initialize()
        
        self.client.login(username=self.u1.username, password='secret')
        post_form_url = "/"+urls["NEW_ARTICLE"]+"/"

        data = {
            'title' : "Lorem ipsum",
            'body' : "Lorem ipsum! Lorem ipsum! Lorem ipsum!",
            'publish' : True,
        }

        response = self.client.post(
                        post_form_url,
                        data,
                   )
        
        self.failUnlessEqual(len(Post.objects.all()), 1)

    def test_my_recommendations(self):
        """
            Test my_recommendations
        """
        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        response = self.client.get("/" + urls["RECOMMENDATIONS"] + "/")
        self.failUnlessEqual(response.status_code, 200)
