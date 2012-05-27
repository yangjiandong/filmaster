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
from django.conf.urls.defaults import *

# @@@ from atom import Feed

from film20.notification.views import notices, notice_settings, mark_all_seen, feed_for_user, single
from film20.config.urls import *

notificationpatterns = patterns('',
#    url(r'^'+urls["MANAGE_NOTIFICATIONS"]+'/$', notice_settings, name="notification_notice_settings"),
#    url(r'^'+urls["NOTIFICATIONS"]+'/$', notices, name="notification_notices"),
#    url(r'^'+urls["NOTIFICATION"]+'/(\d+)/$', single, name="notification_notice"),
#    url(r'^'+urls["NOTIFICATIONS"]+'/'+urls["RSS"]+'/$', feed_for_user, name="notification_feed_for_user"),
#    url(r'^'+urls["MARK_NOTIFICATIONS_AS_READ"]+'/$', mark_all_seen, name="notification_mark_all_seen"),
)
