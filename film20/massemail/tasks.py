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

from celery.task import Task
from django.conf import settings
from film20.massemail.models import MassEmail

TASK_CONFIG = getattr( settings, 'CELERY_MASSMAIL_TASK_CONFIG', {} )

class SendMassEmailTask( Task ):

    def run( self, message, massemail ):
        try:
            # if successfully sent increment sent_correctly 
            #   and add email addresses to sent_correctly_to list
            message.send()
            self.set_message_status( message, massemail, True )

        except:
            try:
                self.retry( [message, massemail] )

            except self.MaxRetriesExceededError:
                # when max retries exceeded we need to increment
                #   sent_failed and add addresses to sent_failed_to list

                self.set_message_status( message, massemail, False )

    def set_message_status( self, message, massemail, sent ):
        massemail = MassEmail.objects.get( pk = massemail.pk )
        if sent:
            count_attr = 'sent_correctly'
            list_attr = 'sent_correctly_to'
        else:
            count_attr = 'sent_failed'
            list_attr = 'sent_failed_to'

        list_ = getattr( massemail, list_attr )
        tmp_list = list_.split( ';' ) if list_ is not None else []

        for to in message.to:
            tmp_list.append( to )

        setattr( massemail, count_attr, len( tmp_list ) )
        setattr( massemail, list_attr, ';'.join( tmp_list ) )

        massemail.save()

# configure task
for key, value in TASK_CONFIG.iteritems():
    setattr( SendMassEmailTask, key, value )
