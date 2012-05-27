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
# Python
import random
import logging
import pytz, datetime

# Django
from django.utils.translation import gettext_lazy as _, gettext
from django.contrib.auth.models import User
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

from film20.facebook_connect.models import FBAssociation
from film20.utils import cache

logger = logging.getLogger(__name__)

from film20.utils.template import Library
register = Library()


@register.inclusion_tag('facebook_connect/fb_like.html', takes_context=True)
def fb_like(context, object):
    content_type = ContentType.objects.get_for_model(object.__class__)

    return {
        'object':object,
        'content_type':"%s.%s" % (content_type.app_label, content_type.model),
    }

@register.inclusion_tag('facebook_connect/invite_box.html', takes_context=True)
def invite_box(context):
    request = context['request']
    assoc = None
    friends = []
    if request.user.is_authenticated():
        try:
            assoc = FBAssociation.objects.select_related('fb_user').get(user=request.user)
            if assoc.fb_user_id:
                key = cache.Key("some_fb_friends", assoc.fb_user_id)
                friends = cache.get(key)
                if friends is None:
                    friends = assoc.fb_user.friends
                    friends = list(friends.exclude(fbassociation__isnull=False).order_by('?')[0:100])
                    cache.set(key, friends)
        except FBAssociation.DoesNotExist, e:
            pass

    return {
            'association': assoc,
            'friends': friends,
            }

@register.inclusion_tag('facebook_connect/fb_connected_users.html')
def connected_users():
    return { 'app_id': settings.FACEBOOK_CONNECT_KEY }

