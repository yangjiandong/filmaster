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
from django import template
from django_openidauth.models import UserOpenID
from django.utils.safestring import mark_safe

register = template.Library()

def openid_icon(openid, user):
    oid = u'%s' % openid
    matches = [u.openid == oid for u in UserOpenID.objects.filter(user=user)]
    if any(matches):
        return mark_safe(u'<img src="/site_media/openid-icon.png" alt="Logged in with OpenID" />')
    else:
        return u''
register.simple_tag(openid_icon)
