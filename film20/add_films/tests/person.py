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

from django.test import TestCase

from film20.add_films.forms import PersonForm

class PersonTest( TestCase ):

    def testPersonIMDBCode( self ):
        
        # empty form is ivalid
        form = PersonForm( {} )
        self.assertEqual( form.is_valid(), False )

        # form with name and surname is OK
        form = PersonForm( { 'name': 'Jack', 'surname': 'Mort' } )
        self.assertTrue( form.is_valid() )
        
        # form with bad code is invalid
        form = PersonForm( { 'name': 'Jack', 'surname': 'Mort', 
                            'imdb_code': 'bad_code' } )
        self.assertEqual( form.is_valid(), False )

        # user can set only code
        form = PersonForm( { 'name': 'Jack', 'surname': 'Mort', 
                            'imdb_code': 'nm1382072' } )
        self.assertTrue( form.is_valid() )
        self.assertEqual( form.cleaned_data['imdb_code'], '1382072' )

        # ... or full url
        form = PersonForm( { 'name': 'Jack', 'surname': 'Mort', 
                            'imdb_code': 'http://www.imdb.com/name/nm1382072' } )
        self.assertTrue( form.is_valid() )
        self.assertEqual( form.cleaned_data['imdb_code'], '1382072' )

        # ... and with slash
        form = PersonForm( { 'name': 'Jack', 'surname': 'Mort', 
                            'imdb_code': 'http://www.imdb.com/name/nm1382072/' } )
        self.assertTrue( form.is_valid() )
        self.assertEqual( form.cleaned_data['imdb_code'], '1382072' )

        # but film code is wrong
        form = PersonForm( { 'name': 'Jack', 'surname': 'Mort', 
                            'imdb_code': 'http://www.imdb.com/title/tt0800080/' } )
        self.assertEqual( form.is_valid(), False )

