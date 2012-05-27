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

import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

import film20.moderation

class ModeratedObject( models.Model ):
    STATUS_UNKNOWN = -1
    STATUS_REJECTED = 0
    STATUS_ACCEPTED = 1

    STATUS_CHOICES = (
        ( STATUS_UNKNOWN, _( "Unknown" ) ),
        ( STATUS_REJECTED, _( "Not accepted" ) ),
        ( STATUS_ACCEPTED, _( "Accepted" ) ),
    )
    
    moderation_status = models.IntegerField( _( "Status" ), choices=STATUS_CHOICES, default=STATUS_UNKNOWN ) 
    moderation_status_at = models.DateTimeField( _( "Moderated at" ), blank=True, null=True )
    moderation_status_by = models.ForeignKey( User, verbose_name=_( "Moderated by" ), 
                                    related_name = "%(class)s_moderated_objects", blank=True, null=True )
    
    rejection_reason = models.TextField( blank=True, null=True )
    
    class Meta:
        abstract = True

    def _set_status( self, status, user, save=True ):
        self.moderation_status = status
        self.moderation_status_by = user
        self.moderation_status_at = datetime.datetime.now()
    
        if save:
            self.save()

    def accept( self, user, **kwargs ):
        self._set_status( ModeratedObject.STATUS_ACCEPTED, user )

    def reject( self, user, reason=None ):
        self._set_status( ModeratedObject.STATUS_REJECTED, user, False )
        if reason is not None:
            self.rejection_reason = reason

        self.save()

