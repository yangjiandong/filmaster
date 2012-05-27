from film20.utils.test import TestCase
from django.utils import unittest
from django.contrib.auth.models import User
from film20.core.models import Film, Object
from film20.blog.models import Post, Blog
from film20.threadedcomments.models import ThreadedComment
from film20.threadedcomments.templatetags.threadedcommentstags import *
from film20.config.urls import *
from film20.utils.utils import proccess_json_response

class ThreadedCommentTestCase(TestCase):

    u1 = None
    film = None

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        # set up post
        self.post = Post()
        self.post.title = "Lorem ipsum"
        self.post.body = "Sialalala tralalal!"
        self.post.type = Object.TYPE_POST
        self.post.permalink = "lorem-ipsum"
        self.post.status = Post.PUBLIC_STATUS
        self.post.user = self.u1
        self.post.save()

    def clean_data(self):
        User.objects.all().delete()
        Post.objects.all().delete()
        Blog.objects.all().delete()
        ThreadedComment.objects.all().delete()

    def test_comments(self):

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        # take url for new comment
        comment_form_url = get_comment_url(self.post)

        data = {
            'comment' : "Tralala bum bum bum",
            'next' : self.post.get_absolute_url()
        }

        # send data
        response = self.client.post(
                        comment_form_url,
                        data,
                        )

        # if success there should be one comment in db
        self.failUnlessEqual(len(ThreadedComment.objects.all()), 1)

        comment = ThreadedComment.objects.get(user=self.u1)

        # try to delete comment
        delete_comment_url = "/"+urls["DELETE_COMMENT"]+'/'+str(comment.id)+"/"

        response = self.client.get(
                        delete_comment_url,
                )
    
    @unittest.skip("comment delete view not available yet")
    def test_comment_delete(self):

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        # take url for new comment
        comment_form_url = get_comment_url(self.post)

        data = {
            'comment' : "Tralala bum bum bum",
            'next' : self.post.get_absolute_url()
        }

        # send data
        response = self.client.post(
                        comment_form_url,
                        data,
                        )

        # if success there should be one comment in db
        self.failUnlessEqual(len(ThreadedComment.objects.all()), 1)

        comment = ThreadedComment.objects.get(user=self.u1)

        # try to delete comment
        delete_comment_url = "/"+urls["DELETE_COMMENT"]+'/'+str(comment.id)+"/"

        response = self.client.get(
                        delete_comment_url,
                )

        comment = ThreadedComment.objects.get(user=self.u1)
        # comment in db should have DELETED_STATUS
        
        self.failUnlessEqual(comment.status, Object.DELETED_STATUS)


    def test_comments_ajax(self):

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        # url for new comment
        comment_form_url = get_comment_url(self.post)

        comment_form_url += 'json/'

        data = {
            'comment' : "Tralala bum bum bum",
        }

        # sending using ajax
        response = self.client.post(
                        comment_form_url,
                        data,
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                        )

        # if everything is ok - response code should be 200
        self.failUnlessEqual(response.status_code, 200)









