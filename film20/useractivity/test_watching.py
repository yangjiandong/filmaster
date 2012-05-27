#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
import unittest
from django.test.client import Client

from django.contrib.auth.models import User
from film20.core.models import Object, Film
from film20.blog.models import Blog, Post
from film20.useractivity.models import *
from film20.useractivity.watching_helper import *
from film20.notification import models as notification
from film20.utils.test import TestCase

class WatchingTestCase(TestCase):
   
    u1 = None
    u2 = None
    u3 = None
    u4 = None
    blog1 = None
    post1 = None
     
    def clean_data(self):
        User.objects.all().delete()
        Watching.objects.all().delete()
        notification.Notice.objects.all().delete()

    def setUp(self):
        Film.objects.filter(imdb_code__lt=1000).delete()
    
    def initialize(self):
        self.clean_data()

        # set up users
        self.u1 = User(username='michuk', email='borys.musielak@gmail.com')
        self.u1.save()
        self.u2 = User(username='adz', email='b.orysmusielak@gmail.com')
        self.u2.save()
        self.u3 = User(username='turin', email='borysm.usielak@gmail.com')
        self.u3.save()
        self.u4 = User(username='olamus', email='borysmu.sielak@gmail.com')
        self.u4.save()
 
        #user self.blog1
        self.blog1 = Blog(user=self.u1)
        self.blog1.save()

        # create a self.post1
        from datetime import datetime
        self.post1 = Post(user=self.u1, title="New Post", type=Object.TYPE_POST, is_public=False, publish=datetime.now())
        self.post1.save()    

    def test_watching_subscribe(self):
        """
            User u4 subscribes to a post by u1. Then a comment is added by another user u2.
            User u4 should receive a notification.
            Then user4 unsubscribes to the same post and user u2 adds one more comment.
            This time the reply notification should not be sent to u4.
        """
        self.initialize()        
     
        # subscribe to this self.post1 by a different user (who haven't commented on it)
        watching_helper = WatchingHelper()
        activity = UserActivity.objects.get_for_object(self.post1)
#        watching_helper.alter_watching_subscribed(self.u4, activity)
        Watching.subscribe(activity, self.u4, True)

        # create a comments for blog post by a different user
        t = ThreadedComment(user=self.u2,
                                comment="This is a comment",
                                content_object=activity, 
                                type=Object.TYPE_COMMENT)
        t.save() 

        # assert all is fine
        watching_objects = Watching.objects.filter(is_observed=True) 
        self.assertEquals(len(watching_objects), 3) # number of unique comments in threads should be equal to watching objects

        reply_notices = notification.Notice.objects.filter(notice_type__label='reply')

        # TODO: uncommend and fix in http://jira.filmaster.org/browse/FLM-1116
        # self.assertEquals(len(reply_notices), 2) # number of notices

        # unsubscribe to the previously subscribed posts
#        watching_helper.alter_watching_subscribed(self.u4, activity)
        Watching.subscribe(activity, self.u4, False)

        # assert the number of observed watching objects is smaler by 1
        watching_objects = Watching.objects.filter(is_observed=True) 
        self.assertEquals(len(watching_objects), 2) # number of unique comments in threads should be equal to watching objects

        # create another comment for blog post by he same user than previously 
        # (should generate 1 reply notification to the author of the post)
        t = ThreadedComment(user=self.u2,
                                comment="This is also a comment, second one by the same user",
                                content_object=activity, 
                                type=Object.TYPE_COMMENT)
        t.save() 
        reply_notices = notification.Notice.objects.filter(notice_type__label='reply')

        # TODO: uncommend and fix in http://jira.filmaster.org/browse/FLM-1116
        self.assertEquals(len(reply_notices), 3) # number of notices
        
    def test_watching_notification(self):
        """
            Testing notifications for different types of activities (posts, short reviews and threads)
        """
        self.initialize()        
        activity = UserActivity.objects.get_for_object(self.post1)

        # create two comments for blog post by two different users 
        t = ThreadedComment(user=self.u2,
                                comment="This is a comment",
                                content_object=activity, 
                                type=Object.TYPE_COMMENT)
        t.save() 
        t = ThreadedComment(user=self.u3,
                                comment="This is also a comment",
                                content_object=activity, 
                                type=Object.TYPE_COMMENT)
        t.save() 
        
        # create film and a short review and a comment to it
        f1 = Film(type=1, permalink='przypadek', imdb_code=111, status=1, version=1, 
            release_year=1999, title='Przypadek', popularity=1, popularity_month=1)
        f1.save()
        sr = ShortReview(user=self.u1, review_text="This is a short review", object = f1, type=Object.TYPE_SHORT_REVIEW)
        sr.save()
        activity2 = UserActivity.objects.get_for_object(sr)
        t = ThreadedComment(user=self.u2,
                                comment="This is a comment to a short review",
                                content_object=activity2, 
                                type=Object.TYPE_COMMENT)
        t.save()

        # assert all is fine
        watching_objects = Watching.objects.all() 
        self.assertEquals(len(watching_objects), 5) # number of unique comments in threads should be equal to watching objects

        reply_notices = notification.Notice.objects.filter(notice_type__label='reply')

        # TODO: uncommend and fix in http://jira.filmaster.org/browse/FLM-1116
        self.assertEquals(len(reply_notices), 4) # number of notices
