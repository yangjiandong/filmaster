from django import forms
from django.forms.util import flatatt
from django.forms.fields import Field
from django.forms.widgets import Widget
from django.utils.encoding import force_unicode
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from film20.core.models import Film
from film20.film_features.models import TYPE_CHOICES


class SimilarFilmWidget( Widget ):

    PERSON_ID = '%s_id'
    PERSON_NAME = '%s_name'
    HTML_ROW = [
        '<div class="row-film">',
            '<div class="img"></div>'
            '<input type="checkbox" name="" class="film_check" %s />',
            '<input type="hidden" name="%s" value="%s" class="film_id" />',
            '<input type="text" name="%s" value="%s" class="film_name" />',
            
            '<a class="remove_row" href="javascript:void(0)">',
            '<img src="/media/img/admin/icon_deletelink.gif" width="10" height="10" alt="Remove Item"/> %s' % _( "remove" ),
            '</a>',
        '</div>'
    ]
    
    CLIENT_CODE = """
        <script type="text/javascript">

        $(document).ready(function () {
            function formatItem( row ) {
                return row[0].replace('&verticalline;','|');
            }
            
            // ---
            var bindFilm = function( el ){
                $( ".remove_row", el ).click( function() {
                    $(this).parent().remove()
                })

                $( ".film_name", el ).autocomplete( '%s', {
                    formatItem: formatItem,
                    formatResult: formatItem
                });

               $( ".film_name", el ).result( function( event, data, formatted ) {
                    $( ".film_id", $(this).parent() ).val( data[3] ).removeAttr( 'disabled' );
                    $( ".film_check", $(this).parent() ).attr( 'checked', 'checked' );
               });
               
               var checked = $( ".film_check", el ).attr( 'checked' );
               if ( checked == 'checked' ) {
                  $( ".film_id", el ).removeAttr( "disabled" );
               } else {
                  $( ".film_id", el ).attr( "disabled", "disabled" );
               }
                
               $( ".film_check", el ).click( function() {
                  if( $( this ).attr( 'checked' ) == 'checked' ) {
                    $( ".film_id", $(this).parent() ).removeAttr( 'disabled' );
                  } else {
                    $( ".film_id", $(this).parent() ).attr( 'disabled', 'disabled' );
                  }
               })
            }

            $('#add_%s').click( function() {
                var el = $( '%s' )
                $("#id_%s").append( el )
                // ..
                bindFilm( el )
            })

            bindFilm( $( ".row-film" ) )
        });
        </script>
        """

    def render( self, name, value, attrs=None ):
        if value is None: 
            value = []
        
        final_attrs = self.build_attrs( attrs, name=name )
        output = [ u'<div class="film_content" id="id_%s">' % name ]

        for v in value:
            output.append( ''.join( self.HTML_ROW ) % ( 
                '' if getattr( v, 'suggestion', False ) else 'checked="checked"',
                self.PERSON_ID % name, v.pk,
                self.PERSON_NAME % name, str( v )
            ) )

        output.append( u'</div><a id="add_%s" href="javascript:void(0);" class="add_film"><img src="/media/img/admin/icon_addlink.gif" width="10" height="10" alt="[+]"/> %s</a><div style="clear:both"></div>' % ( name, _( "add film" ) ) )
        
        return mark_safe( u'\n'.join( output ) + 
                         ( self.CLIENT_CODE % ( reverse( 'search_film_autocomplete' ), name, 
                                               ( ''.join( self.HTML_ROW ) % ( 'checked="checked"', self.PERSON_ID % name, 
                                                 '', self.PERSON_NAME % name, '' ) ), name
                                              ) ) )

    def value_from_datadict( self, data, files, name ):
        if data.has_key( self.PERSON_ID % name ):
            return data.getlist( self.PERSON_ID % name )
        return []


class SimilarFilmField( Field ):
    widget = SimilarFilmWidget

    def clean( self, value ):
        ids = []
        result = []
        for id in value:
            try:
                result.append( Film.objects.get( pk=int( id ) ) )

            except:
                raise forms.ValidationError( _( 'Invalid selection' ) )
        
            # person must by unique
            if id in ids:
                raise forms.ValidationError( _( 'The same film can be selected only once' ) )
        
            ids.append( id )

        if self.required and len( result ) == 0:
            raise forms.ValidationError( _( 'This field is required' ) )
        
        return result



class FeaturesWidget( Widget ):
    def __init__( self, attrs=None ):
        super( FeaturesWidget, self ).__init__( attrs )
        self.choices = TYPE_CHOICES
    
    def decompress( self, value ):
        return value.split( ',' )
    
    def render( self, name, value, attrs=None ):
        if value is None:
            value = ''
        output = []
        selected = self.decompress( value )
        has_id = attrs and 'id' in attrs
        for i, choice in enumerate( self.choices ):
            v, l = choice
            final_attrs = self.build_attrs( attrs, type='checkbox', name=name )
            final_attrs['value'] = force_unicode( v )
            if str( v ) in selected:
                final_attrs['checked'] = 'checked'
            if has_id:
                final_attrs['id'] = '%s_%s' % ( attrs['id'], i )
            output.append( u'<input%s /> %s' % ( flatatt( final_attrs ), l ) )
        return mark_safe( '<div id="id_features">%s</div>' % ''.join( [ '<p>%s<p/>' % i for i in output ] ) )
    
    def value_from_datadict( self, data, files, name ):
        if not data.has_key( name ):
            return ''
        values = data.getlist( name )
        return ','.join( values ) if values else ''


class FilmFeaturesForm( forms.Form ):
    similar_films = SimilarFilmField( label=_( "Similar Films" ), required=False )
    features = forms.CharField( label=_( "Film Features" ), required=False, widget=FeaturesWidget )

    def as_div( self ):
        return self._html_output(
            normal_row = u'<div class="col">%(errors)s<h1>%(label)s</h1> %(field)s%(help_text)s</div>',
            error_row = u'<li>%s</li>',
            row_ender = '</li>',
            help_text_html = u' <span class="helptext">%s</span>',
            errors_on_separate_row = False)

