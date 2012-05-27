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
# Threadlocals middleware
# Solution based on: http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def get_current_user():
    try:
        return _thread_locals.request.user
    except AttributeError:
        return None

def get_request():
    try:
        return _thread_locals.request
    except:
        return None

class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage.
    mrk: store request instead of user, because accessing user 
         access session too so Vary: Cookie header is always added
    """
    
    def process_request(self, request):
        _thread_locals.request = request
