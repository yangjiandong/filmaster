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
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.core.models import *


def rebuild_searchkeys():
    rebuild_film_searchkeys()
    rebuild_person_searchkeys()

def rebuild_film_searchkeys():
    print "creating film search keys..."
    for f in Film.objects.iterator():
        f.save()
    print "done."
    print "creating localized film search keys..."
    for f in FilmLocalized.objects.iterator():
        f.save()
    print "done."
        
def rebuild_person_searchkeys():
    print "creating person search keys..."
    for p in Person.objects.iterator():
        p.save()
    print "done."
    print "creating person localized search keys..."
    for p in PersonLocalized.objects.iterator():
        p.save()
    print "done."
        
if __name__ == "__main__":
    rebuild_searchkeys()
