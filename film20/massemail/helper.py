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

from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMessage;

from film20.core.models import Profile
from film20.massemail.tasks import SendMassEmailTask

def sendMassEmail( massemail ):
    """
    Sends message to users with given locale
    """

    profiles = Profile.objects.filter( ~Q( user__email="" ), LANG=massemail.lang ).exclude( user=massemail.created_by ).exclude( user__is_active=False )

    if massemail.mobile_platform is not None:
        profiles = profiles.filter( mobile_platform=massemail.mobile_platform )

    # exclude already sended items
    if massemail.sent_correctly > 0:
        for sended_to in massemail.sent_correctly_to.split( ';' ):
            profiles = profiles.exclude( user__email=sended_to )

    for profile in profiles:
        message = EmailMessage( massemail.subject, massemail.body, 
                           settings.DEFAULT_FROM_EMAIL, [profile.user.email] )
        message.content_subtype = "html"
        print "sending email to: " + profile.user.email
        SendMassEmailTask.delay( message, massemail )

