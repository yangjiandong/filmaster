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

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from film20.core.models import Profile

def mobile_platform_choices():
    return ( ( name, name ) for _, name in settings.USER_AGENTS )

class MassEmail( models.Model ):
    
    subject = models.CharField( _( "Subject" ), max_length=100 )
    body = models.TextField( _( "Body" ) )
    is_processed = models.BooleanField()
    
    lang = models.CharField( _( "Language" ), max_length=2, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE )
    mobile_platform = models.CharField( _( "Mobile platform" ), max_length=16, choices=mobile_platform_choices(), blank=True, null=True  )

    created_at = models.DateTimeField( _( "Created at" ), auto_now_add=True )
    created_by = models.ForeignKey( User, verbose_name=_( "Created by" ), blank=True, null=True )
    
    sent_failed = models.IntegerField( _( "Sent failed" ), default=0 )
    sent_correctly = models.IntegerField( _( "Sent correctly" ), default=0 )

    sent_failed_to = models.TextField( _( "Sent failed to" ), blank=True, null=True )
    sent_correctly_to = models.TextField( _( "Sent correctly to" ), blank=True, null=True )

    class Meta:
        ordering = [ "-created_at", "subject" ]
        verbose_name = _( "Mass Email" )
        verbose_name_plural = _( "Mass Emails" )

