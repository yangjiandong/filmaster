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

from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

class QueueManager( models.Manager ):

    def get_for_language( self, lang=settings.LANGUAGE_CODE ):
        return self.get_query_set().filter( LANG=lang )

    def add_to_queue( self, obj, action_type, lang=settings.LANGUAGE_CODE ):
        content_type = ContentType.objects.get_for_model( obj )
        try:
            item = self.get( content_type = content_type, \
                            object_id = obj.pk, LANG=lang )

        except self.model.DoesNotExist:
            item = self.model( content_type = content_type, \
                              object_id = obj.pk, LANG=lang )
        except self.model.MultipleObjectsReturned:
            self.filter( content_type = content_type, \
                            object_id = obj.pk, LANG=lang ).delete()
            item = self.model( content_type = content_type, \
                              object_id = obj.pk, LANG=lang )

        item.modified_at = datetime.now()
        item.action_type = action_type

        item.save()
        
class QueuedItem( models.Model ):
    ACTION_UPDATED = 1
    ACTION_REMOVED = 2

    ACTION_CHOICES = (
        ( ACTION_UPDATED, _( "Updated" ) ),
        ( ACTION_REMOVED, _( "Removed" ) ),
    )
    
    modified_at = models.DateTimeField( _( "Modified at" ) )
    action_type = models.IntegerField( _( "Action type" ), choices=ACTION_CHOICES )

    content_type = models.ForeignKey( ContentType )
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey( 'content_type', 'object_id' )
    
    LANG = models.CharField( max_length=2, default=settings.LANGUAGE_CODE )

    objects = QueueManager()
