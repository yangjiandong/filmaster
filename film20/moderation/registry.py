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

from film20.moderation.items import ModeratedItem, ModeratorTool

class AlreadyRegistered( Exception ):
    pass

class ModerateRegistry( object ):

    def __init__( self ):
        self._registry_all = {}
        self._registry = {
            'items': {},
            'tools': {}
        }

    def register( self, moderated_item ):
        if not isinstance( moderated_item, ModeratedItem ):
            raise AttributeError( "The registered class %s must be instance of ModeratedItem." % moderated_item )

        name = str( moderated_item.get_name() )
        if name in self._registry_all:
            raise AlreadyRegistered( 'The item with same name ( %s ) is already registered' % name )

        if isinstance( moderated_item, ModeratorTool ):
            moderated_item.is_tool = True
            self._registry['tools'][name] = moderated_item
        else:
            moderated_item.is_tool = False
            self._registry['items'][name] = moderated_item
        
        self._registry_all[name] = moderated_item

    def get_all( self ):
        return self._registry_all
    
    def get_by_name( self, name ):
        # in some cases name is displayed as 'functionProxy' wtf ?
        key = str( name ) 
        if not self._registry_all.has_key( key ):
            return None

        return self._registry_all[ key ]

    def get_by_user( self, user ):
        items = { 
            'items': [],
            'tools': [],
        }
        for model, item in self._registry_all.items():
           if user.has_perm( item.permission ):
               items[ 'tools' if item.is_tool else 'items' ].append( item )
        return items

registry = ModerateRegistry()
