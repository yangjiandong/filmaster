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
from film20.utils.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.core.models import ShortReview
from film20.blog.models import Post
from film20.useractivity.models import UserActivity

class UserTestCase(TestCase):
    fixtures = ['test_users.json']
    def test_user_deactivate(self):
        client = Client()
        user = User.objects.get(username='test')
        
        ShortReview.objects.create(
            kind=ShortReview.WALLPOST,
            user=user,
            review_text='wall post text',
            type=ShortReview.TYPE_SHORT_REVIEW,
        )
        
        post = Post.objects.create(
            user=user,
            title='post title',
            body='post body',
        )

        post_url = reverse('show_article', args=[user.username, post.permalink])
        response = client.get(post_url)
        self.assertEquals(response.status_code, 200)
        
        self.assertEquals(UserActivity.objects.public().filter(user=user).count(), 2)
        
        user.is_active = False
        user.save()

        self.assertEquals(UserActivity.objects.public().filter(user=user).count(), 0)
        
        response = client.get(post_url + '?skip_cache')
        self.assertEquals(response.status_code, 404)
