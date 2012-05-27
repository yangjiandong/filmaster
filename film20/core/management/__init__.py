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
from django.db.models import get_models, signals, get_app
from django.conf import settings
from django.utils.translation import ugettext_noop as _
from django.core.exceptions import ImproperlyConfigured

try:
    notification = get_app('notification')
    TYPE_USER_ACTIVITY = notification.NoticeType.TYPE_USER_ACTIVITY
        
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("useractivity_films_rated", _("You rated a movie"), _("films rated"), default=1, type=TYPE_USER_ACTIVITY)
        notification.create_notice_type("useractivity_just_joined", _("You have just joined filmaster"), _("just joined filmaster"), default=1, hidden=True, type=TYPE_USER_ACTIVITY)
        notification.create_notice_type("username_mentioned", _( "Someone mentioned your nick" ), _( "nick mentioned" ) )
        notification.create_notice_type( "trailer_to_remove_moderated", _( "Trailer to remove moderated" ), _( "requested trailer to remove has been moderated" ) )
    
    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImproperlyConfigured:
    print "Skipping creation of NoticeTypes as notification app not found"
