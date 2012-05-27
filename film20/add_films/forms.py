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

import datetime, re

from django import forms
from django.forms.util import ErrorList
from django.utils.translation import gettext_lazy as _
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import SimpleUploadedFile

from film20.core.models import Person, Film
from film20.add_films.models import AddedFilm, AddedCharacter
from film20.add_films.fields import DirectorsField, ActorsField, CountriesField, ImageField


class PersonForm( forms.ModelForm ):
    name = forms.CharField( label=_( "Name" ), max_length=50 )
    surname = forms.CharField( label=_( "Surname" ), max_length=50 )
    imdb_code = forms.CharField( label=_( "IMDB url"), required=False, max_length=128,
                                help_text=_( "If the person you're adding has a page on IMDB.com, please provide their IMDB url" ) )

    class Meta:
        model = Person
        fields = ( 'name', 'surname', 'imdb_code' )

    def clean_imdb_code( self ):
        imdb_code = self.cleaned_data['imdb_code']
        if imdb_code.strip() == '':
            return None

        line = re.match( '.*nm(\d+)', imdb_code )
        if line <> None:
            return line.group( 1 ).strip()
        
        raise forms.ValidationError( _( "invalid imdb code" ) )
    
    def as_p( self ):
        return self._html_output( u'<p>%(label)s %(help_text)s%(field)s</p>', u'%s', '</p>', 
                                 u'<span class="help-text">%s</span>', True )

class FilmCastForm( forms.ModelForm ):
    """
    Form to add, edit film cast
    """
    def __init__( self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None ):

        if instance is not None:
            if initial is None:
                initial = {}

            initial['directors'] = [ ( d.person.id, str( d.person ) ) for d in instance.directors.all() ]
            initial['actors'] = [ ( ch.person.id, str( ch.person ), ch.character ) for ch in instance.get_actors() ]

        super( FilmCastForm, self ).__init__( data, files, auto_id, prefix, initial,
                                            error_class, label_suffix, empty_permitted, instance )

    directors = DirectorsField( label=_( "Directors" ) )
    actors = ActorsField( label=_( 'Actors' ), required=False )

    class Meta:
        model = Film
        fields = (
            'directors',
            'actors',
        )

class AddFilmForm( forms.ModelForm ):
    def __init__( self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None ):

        if instance is not None:
            # we must manually update actors and countries
            if initial is None:
                initial = {}

            initial['directors'] = [ ( d.person.id, str( d.person ) ) for d in instance.directors.all() ]

            initial['actors'] = [ ( ch.person.id, str( ch.person ), ch.character ) \
                                 for ch in instance.get_actors() ]

            initial['production_country'] = [ c.country for c in instance.production_country.all() ]

        super( AddFilmForm, self ).__init__( data, files, auto_id, prefix, initial,
                                            error_class, label_suffix, empty_permitted, instance )

    """
    Form to manualy add, edit film
    """
    production_country = CountriesField( label=_( "Production Countries (we will hint when you start typing)" ) )
    directors = DirectorsField( label=_( "Director (we will hint when you start typing)" ) )
    actors = ActorsField( label=_( "Actors (we will hint when you start typing)" ), required=False  )
    image = ImageField( required=False, label=_( "Image" ), help_text=_( "JPG, PNG, GIF - Max: 5MB" )  )

    class Meta:
        model = AddedFilm
        fields = ( 
            'type',
            'title',
            'localized_title',
            'release_year',
            'completion_year',
            'directors', 
            'production_country',
            'image',
            'actors'
        )
    
    def clean_release_year( self ):
        year = self.cleaned_data['release_year']
        current_year = datetime.datetime.today().year

        if year < 1890 or year > current_year + 1:
            raise forms.ValidationError( _( "year must be in range 1890  current year + 1" ) )
        
        return year
