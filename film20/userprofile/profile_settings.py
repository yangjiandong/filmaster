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
from os.path import join

AVATARS_DIR = join(settings.MEDIA_ROOT, 'img/avatars')
DEFAULT_AVATAR = getattr(settings, "DEFAULT_AVATAR", os.path.join(settings.MEDIA_ROOT, "img/avatars/generic.jpg"))
DEFAULT_AVATAR_WIDTH = 96
AVATAR_WEBSEARCH = False
# filmaster.pl key
#GOOGLE_MAPS_API_KEY = "ABQIAAAAKrt0-aQc0WGSPvVB-A45kxT-242ipLOhUj9S3MlChUBhryyR1RQrwzQ3hAhrDnibAw_DSQZfKSs6wg"
# film20.jakilinux.org key
GOOGLE_MAPS_API_KEY = "ABQIAAAAKrt0-aQc0WGSPvVB-A45kxShtuydGFzn4f5eCwWcaIompoWaGRSLgYz4rez0510WwLdNwBFSTjMOhQ"
