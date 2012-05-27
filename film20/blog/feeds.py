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
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.template import loader, Context
from django.template import loader, Context
from django.http import HttpResponse

from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.syndication.feeds import Feed
from django.shortcuts import get_object_or_404
from film20.blog.models import Post
from django.template.defaultfilters import linebreaks, escape, capfirst
from datetime import datetime
from django.contrib.syndication.feeds import FeedDoesNotExist

class LatestPosts(Feed):
    title = "test"
    link = "blog/feed"
    description = "test"
    
    def get_object(self, params):
        print params
        return get_object_or_404(User, username=params[0].lower())

    def items(self, username):
        return Post.objects.filter(author=username).order_by("-created_at")
