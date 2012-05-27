# coding=UTF-8

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

from django.conf import settings

from film20.userprofile.models import Avatar, AVATAR_SIZES

try:
    from PIL import Image
except:
    import Image

import os
import logging
logger = logging.getLogger(__name__)

from film20.utils import cache_helper as cache

DEFAULT_AVATAR = getattr(settings, "DEFAULT_AVATAR",
                         os.path.join(settings.MEDIA_ROOT, "img/avatars/generic.jpg"))

def get_avatar_path(user, size, **kw):
    url = None
    is_username = isinstance(user, basestring)
    
    if settings.CACHE_AVATARS:
        key = cache.Key("avatar", str(user), str(size))
        url = cache.get(key)

        # FLM-694
        if url is not None and not os.path.exists( os.path.join( settings.MEDIA_ROOT, url ) ):
            logger.debug( "cached avatar %s does not exists ! [REMOVING]" % url )
            url = None
            cache.delete(key)

    if not url:
        avatar_path = DEFAULT_AVATAR
        try:
            # if is_username is True, user variable is username as text, used by
            # useractivities
            if is_username:
                avatar = Avatar.objects.get(user__username=user, valid=True).image
            else:
                avatar = Avatar.objects.get(user=user, valid=True).image
            if avatar:
                path = os.path.join(settings.MEDIA_ROOT, unicode(avatar))
                if os.path.isfile(path):
                    avatar_path = path
        except Avatar.DoesNotExist:
            pass
        
        path, ext = os.path.splitext(avatar_path)
        thumb_path = "%s.%s%s" % (path, size, ext)
        valid = True
        if not os.path.isfile(thumb_path):
            try:
                image = Image.open(avatar_path)
                image.thumbnail((size, size), Image.ANTIALIAS)
                image.save(thumb_path, "JPEG")
                logger.debug("new avatar generated: %s", thumb_path)
            except IOError, e:
                logger.warning(e)
                valid = False
        url = thumb_path.replace(settings.MEDIA_ROOT, '')
        # eventually cache (if caching allowed)
        if settings.CACHE_AVATARS and valid and url:
            cache.set(key, url)
            logger.debug("Storing avatar in cache under %s" % key)

    return settings.MEDIA_URL + url
