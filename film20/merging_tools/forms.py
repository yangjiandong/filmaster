import re

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import gettext_lazy as _

from film20.config.urls import urls
from film20.core.models import Film, Person

class FilmasterURLField( forms.URLField ):
    verify_exists = True


class ReportDuplicateForm( forms.Form ):

    objectA = FilmasterURLField( label='A' )
    objectB = FilmasterURLField( label='B' )

    PATTERN = ''

    def parseFromUrl( self, url ):
        return None

    def clean_objectA( self ):
        return self.parseFromUrl( self.cleaned_data['objectA'] )

    def clean_objectB( self ):
        return self.parseFromUrl( self.cleaned_data['objectB'] )

    def clean( self ):
        cleaned_data = self.cleaned_data
        objectA = cleaned_data.get( 'objectA' )
        objectB = cleaned_data.get( 'objectB' )

        if objectA is not None and objectB is not None and objectA == objectB:
            raise forms.ValidationError( _( "You must enter different object URLs" ) )

        return cleaned_data

    def _parse( self, url ):
        matcher = re.search( self.PATTERN, url )
        if not matcher:
            raise forms.ValidationError( _( "The URL you entered is not valid object URL" ) )
        return matcher.group( 'permalink' )


class ReportPersonDuplicateForm( ReportDuplicateForm ):

    PATTERN = r'%s/%s/(?P<permalink>[\w\-_]+)' % ( settings.DOMAIN, urls['PERSON'] )

    def parseFromUrl( self, url ):
        permalink = self._parse( url )

        try:
            return Person.objects.get( permalink=permalink )
        except Person.DoesNotExist:
            raise forms.ValidationError( _( "Person does not exist" ) )

    @property
    def url( self ):
        return reverse( 'request-duplicate-person' )

class ReportFilmDuplicateForm( ReportDuplicateForm ):

    PATTERN = r'%s/%s/(?P<permalink>[\w\-_]+)' % ( settings.DOMAIN, urls['FILM'] )

    def parseFromUrl( self, url ):
        permalink = self._parse( url )

        try:
            return Film.objects.get( permalink=permalink )
        except Film.DoesNotExist:
            raise forms.ValidationError( _( "Film does not exist" ) )

    @property
    def url( self ):
        return reverse( 'request-duplicate-movie' )
