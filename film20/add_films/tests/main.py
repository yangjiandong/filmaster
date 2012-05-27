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
import unittest

from django.core.urlresolvers import reverse

from film20.add_films.tests.base import BaseTest
from film20.add_films.models import AddedCharacter, AddedFilm

class MainTest( BaseTest ):

    def testNoLoginAccess( self ):

        self.client.login( username='user', password='user' )
        response = self.client.get( reverse( 'add-film-manual' ) )
        self.assertEqual( response.status_code, 200 )

        self.client.logout()
        response = self.client.get( reverse( 'add-film-manual' ) )
        self.assertEqual( response.status_code, 302 )


    def testAddFilmWithModeration( self ):

        added_film = AddedFilm( title = 'Test film', localized_title='Test film PL', 
                               release_year = 2010, user = self.u1 )
        added_film.save()


        added_film.directors.add( self.p1 )
        added_film.directors.add( self.p2 )

        added_film.production_country.add( self.c1 )
        added_film.production_country.add( self.c2 )
        
        added_film.save()
        
        AddedCharacter.objects.create( added_film=added_film, person=self.p1, character="Test character 1" )
        AddedCharacter.objects.create( added_film=added_film, person=self.p2, character="Test character 2" )
        AddedCharacter.objects.create( added_film=added_film, person=self.p3, character="Test character 3" )
        
        self.assertEqual( len( added_film.get_actors() ), 3 )

        self.assertTrue( added_film.film is None )
        self.assertEqual( added_film.moderation_status, AddedFilm.STATUS_UNKNOWN )

        added_film.accept( self.u2 )

        self.assertTrue( added_film.film is not None )
        self.assertEqual( added_film.moderation_status, AddedFilm.STATUS_ACCEPTED )
        
        film = added_film.film

        self.assertEqual( film.permalink, "test-film" )
        
        
        self.assertTrue( self.p1 in film.top_directors() )
        self.assertTrue( self.p2 in film.top_directors() )

        self.assertEqual( film.get_localized_title(), "Test film PL" )
        
        self.assertEqual( film.production_country_list, "USA,Poland" )
        
        self.assertEqual( len( film.get_actors() ), 3 )


