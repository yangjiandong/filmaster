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
from django.db.models import signals as djsignals

from django.utils.translation import ugettext_noop as _

try:
    from film20.notification import models as notification
    TYPE_USER_ACTIVITY = notification.NoticeType.TYPE_USER_ACTIVITY
            
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("reply", _("New reply"), _("you have received a reply"), default=2)
        notification.create_notice_type("useractivity_post", _("You published an article or review"), _("new review"), default=1, type=TYPE_USER_ACTIVITY)
        notification.create_notice_type("useractivity_short_review", _("You published a wall post"), _("new short review"), default=1, type=TYPE_USER_ACTIVITY)
    
    djsignals.post_syncdb.connect(create_notice_types, sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
