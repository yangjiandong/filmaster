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
        notification.create_notice_type("showtimes_cinemas_found", _("New cinemas detected around you"), _("new cinemas found around"), default=2)
        notification.create_notice_type("useractivity_check_in", _("You checked-in to a movie"), _("check-in"), default=0, type=TYPE_USER_ACTIVITY)
        notification.create_notice_type("useractivity_check_in_cancel", _("You cancelled your movie check-in"), _("check-in cancel"), default=0, type=TYPE_USER_ACTIVITY)

        notification.create_notice_type("showtimes_following_check_in", _("Your friend checked-in to a movie"), _("following user check-in"), default=0)
        notification.create_notice_type("showtimes_following_check_in_cancel", _("Your friend canceled their movie check-in"), _("following user check-in cancel"), default=0)
        notification.create_notice_type("showtimes_near_cinema_check_in", _("Someone around you checked in"), _("near cinema check-in"), default=0)
        notification.create_notice_type("showtimes_near_cinema_check_in_cancel", _("Someone around you cancelled their check-in"), _("near cinema check-in cancel"), default=0)
        notification.create_notice_type("showtimes_following_near_cinema_check_in", _("Your friend checked-in somewhere around you"), _("following user near cinema check-in"), default=2)
        notification.create_notice_type("showtimes_following_near_cinema_check_in_cancel", _("Your friend cancelled their check-in somewhere around you"), _("following user near cinema check-in cancel"), default=1)

        notification.create_notice_type("showtimes_screening_check_in", _("Someone checked-in to your screening"), _("screening check-in"), default=2)
        notification.create_notice_type("showtimes_screening_check_in_cancel", _("Someone cancelled their check-in to your screening"), _("screening check-in cancel"), default=1)
        notification.create_notice_type("showtimes_daily_recommendations", _("Daily recommendations"), _("Daily recommendations"), default=1)
        notification.create_notice_type("showtimes_weekly_recommendations", _("Weekly recommendations"), _("Weekly recommendations"), default=2)
    
    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImproperlyConfigured:
    print "Skipping creation of NoticeTypes as notification app not found"
