import re

from django import forms
from django.utils.translation import gettext_lazy as _

from film20.import_films.models import FilmToImport


IMDB_URL_RE = re.compile( r'^http://www.imdb.com/title/tt.*$' )

class ImdbUrlField( forms.RegexField ):
    default_error_messages = {
        'invalid': _( 'This field must start with "http://www.imdb.com/title/tt"' )
    }

    def __init__( self, *args, **kwargs ):
        super( ImdbUrlField, self).__init__( IMDB_URL_RE, min_length=23, *args, **kwargs )

class FilmToImportForm(forms.ModelForm):
    imdb_url = ImdbUrlField()

    class Meta:
        model = FilmToImport
        exclude = ('user','imdb_id','is_imported','created_at','LANG','status','attempts')
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(FilmToImportForm, self).__init__(*args, **kwargs)
