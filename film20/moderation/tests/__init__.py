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

from film20.moderation.tests.moderated_item import *
from film20.moderation.tests.tagging_tools import *
from film20.moderation.tests.views import *

from django.core.management import call_command
from django.db.models import loading
from django.conf import settings

# FIXME hack to add test models to db
#       find better way to do this
settings.INSTALLED_APPS.append( 'film20.moderation.tests' )
loading.cache.loaded = False

__test__ = {
    'moderated_items': moderated_item,
    'tagging_tools': tagging_tools,
    'views': views,
}
