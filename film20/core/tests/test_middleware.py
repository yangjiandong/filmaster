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
from django.test.client import Client, RequestFactory
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.core.models import ShortReview
from film20.blog.models import Post
from film20.useractivity.models import UserActivity

from film20.utils.test import TestCase

from django.conf.urls.defaults import patterns, url
from django.conf import settings


from django.http import HttpResponse
from django.views.decorators.cache import never_cache

def test_view(request, assert_auth=False):
    assert not assert_auth or request.user.is_authenticated()
    import random
    return HttpResponse("%s %s" % (random.randrange(2**64), request.user))

postcommit_cnt = 0
def on_postcommit(sender, instance, created, *args, **kw):
    global postcommit_cnt
    postcommit_cnt += 1

def test_postcommit_view(request, assert_auth=False):
    User.objects.create(username='postcommittest')
    global postcommit_cnt
    assert postcommit_cnt == 0
    return HttpResponse('ok')

from film20.urls import urlpatterns

urlpatterns += patterns('', 
    url('^test/$', test_view),
    url('^test/postcommit/$', test_postcommit_view),
    url('^assert_auth/$', test_view, {'assert_auth':True}),
)

class MiddlewareTestCase(TestCase):
    fixtures = ['test_users.json']
    urls = 'film20.core.tests.test_middleware'

    def setUp(self):
        self.user = User.objects.get(username='test')
        self.user.set_password('test')
        self.user.save()

        self.client = Client()
        
        self.auth_client = Client()
        self.auth_client.login(username='test', password='test')

    def test_middleware(self):
        settings.DEBUG_PROPAGATE_EXCEPTIONS = True
        
        response = self.auth_client.get('/')
        request = response.context[0]['request']
        
        from film20.middleware.threadlocals import get_current_user

        # few middleware-depended checks

        self.assertTrue(get_current_user() == self.user)
        
        self.assertTrue(isinstance(request.openids, list))
        
        self.assertTrue(request.openid is None)

    def test_cache_middleware(self):
        self.auth_client.get('/assert_auth/')

        response1 = self.auth_client.get('/test/')
        response2 = self.auth_client.get('/test/')
        
        self.assertNotEqual(response1.content, response2.content)

        response1 = self.client.get('/test/')
        response2 = self.client.get('/test/')
        
        self.assertEquals(response1.content, response2.content)

        response1 = self.client.get('/test/', HTTP_HOST='host1')
        response2 = self.client.get('/test/', HTTP_HOST='host2')
        
        self.assertNotEqual(response1.content, response2.content)

    def test_postcommit_middleware(self):
        from film20.core.signals import post_commit
        from film20.core.models import User
        post_commit.connect(on_postcommit, sender=User)
        global postcommit_cnt
        postcommit_cnt = 0

        # object saved inside view
        response = self.client.get('/test/postcommit/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(postcommit_cnt, 1)

        # object saved outside of view, postcommit signal should be sent instantly
        User.objects.create(username='postcommittest2')
        self.assertEquals(postcommit_cnt, 2)


