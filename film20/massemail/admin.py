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

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from film20.massemail.models import MassEmail

class MassEmailAdmin( admin.ModelAdmin ):
    date_hierarchy = 'created_at'
    fieldsets = (
        ( None, {
            'fields': ( 'subject', 'body', 'lang', 'mobile_platform' )
        }),
        ( 'Sending statistics', {
            'classes': ( 'collapse', ),
            'fields': ( 'sent_correctly', 'sent_failed', 'sent_correctly_to', 'sent_failed_to' )
        })
    )
    list_display = ( 'subject', 'created_by', 'created_at', 'lang', 'mobile_platform', 'is_processed', 'sent_stats' )

    def sent_stats( self, obj ):
        return "%d/%d" % ( obj.sent_correctly, obj.sent_correctly + obj.sent_failed )
    
    def save_model( self, request, obj, form, change ):
        if change:
            # not raise an exception anymore - we can now edit but shall not zero the stats 
            # (it may be that half of messages were sent successfully already and then it broke for some reason)
            obj.save()
        else:
            # readonly fields are not supported
            obj.sent_correctly = 0
            obj.sent_failed = 0
            obj.sent_correctly_to = ""
            obj.sent_failed_to = ""
            obj.created_by = request.user
            obj.save()

admin.site.register( MassEmail, MassEmailAdmin );
