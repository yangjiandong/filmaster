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

from film20.core.management.base import BaseCommand

from film20.massemail.models import MassEmail
from film20.massemail.helper import sendMassEmail

class Command( BaseCommand ):
    help = "Sends the massemails."
    
    def handle( self, **options ):
        for massemail in MassEmail.objects.filter( is_processed=False ):
            massemail.is_processed = True
            massemail.save()

            sendMassEmail( massemail )
