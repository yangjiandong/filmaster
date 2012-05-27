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
from film20.config.urls import templates  
from film20.useractivity.models import UserActivity
from film20.blog.models import Post
from django.template import loader, Context
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.models import User

def public_rss(request, username, all=True, reviews=False, short_reviews=False, comments=False, links=False):
    try:
        user = User.objects.get(username__iexact=username, is_active=True)
        profile = user.get_profile()
    except:
        raise Http404
        
    activty_list=[]
    if all==True:
        activty_list = UserActivity.objects.select_related().filter(user=user).exclude(activity_type = UserActivity.TYPE_RATING).exclude(post__status=Post.DRAFT_STATUS).exclude(post__status=Post.DELETED_STATUS).order_by("-created_at")
    if reviews==True:
        activty_list = UserActivity.objects.select_related().filter(user=user, activity_type = UserActivity.TYPE_POST).exclude(post__status=Post.DRAFT_STATUS).exclude(post__status=Post.DELETED_STATUS).order_by("-created_at")
    if short_reviews==True:
        activty_list = UserActivity.objects.select_related().filter(user=user, activity_type = UserActivity.TYPE_SHORT_REVIEW).order_by("-created_at")
    if comments==True:
        activty_list = UserActivity.objects.select_related().filter(user=user, activity_type = UserActivity.TYPE_COMMENT).order_by("-created_at")
    if links==True:
        activty_list = UserActivity.objects.select_related().filter(user=user, activity_type = UserActivity.TYPE_LINK).order_by("-created_at")

    activities = activty_list
    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['PLANET_RSS'])
    c = Context({'activities': activities,'profile':profile})
    response.write(t.render(c))
    return response    
