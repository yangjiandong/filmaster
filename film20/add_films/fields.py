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

from django import forms
from django.forms import fields, widgets
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.datastructures import MultiValueDict, MergeDict

from film20.core.models import Person, Country
from film20.add_films.models import AddedCharacter

class PersonWidget( widgets.MultiWidget ):
    CLIENT_CODE = """
    <a
        href="%s"
        class="add-another"
        onclick="return showAddAnotherPopup(this);">
        <img src="/static/img/icon_addlink.gif" width="10" height="10" alt="Add Another"/>
    </a>

    <script type="text/javascript">
    $( function() {
        function formatItem( row ) {
            return row[1];
        }
        
        function formatResult( row ) {
            return row[1];
        }
        
        $( "#%s" ).autocomplete( '%s', {
            mustMatch: true,
            formatItem: formatItem,
            formatResult: formatResult
        });
        
        $( "#%s" ).result( function( event, data, formatted ) {
            $("#%s").val( data[0] );
        });
    });
    </script>
    """

    class Media:
        js = [
            '/media/js/admin/RelatedObjectLookups.js',
        ]

    def __init__( self, attrs=None ):
        w = ( widgets.HiddenInput( attrs=attrs ),
                   widgets.TextInput( attrs=attrs ) )
        super( PersonWidget, self ).__init__( w, attrs )
    
    def render(self, name, value, attrs=None):
        rendered = super( PersonWidget, self ).render( name, value, attrs )

        id = 'id_%s_1' % name
        hidden_id = 'id_%s_0' % name
        url = reverse( 'person-list-ajax' )
        add_url = reverse( 'add-person-manual' )

        return mark_safe( rendered + ( self.CLIENT_CODE % ( add_url, id, url, id, hidden_id ) ) )

    def decompress( self, value ):
        if value is None:
            return [ None, None]
        
        try:
            id = int( value )
            person = Person.objects.get( pk=id )
            return [id, '%s %s' % ( person.name, person.surname)]
        except:
            return [None, None]

class DirectorsWidget( widgets.Widget ):

    CLIENT_CODE = """
    <script type="text/javascript">
    $('document').ready(function () {
        function formatItem( row ) {
            return row[1];
        }
        
        function formatResult( row ) {
            return row[1];
        }
        // --- sortable
        $(".directors_content").sortable({handle : '.handle', items: '.row-d', axis: 'y' });

        // ---
        var bindDirector = function( el ){
            $( ".remove_row", el ).click( function() {
                $(this).parent().remove()
            })

            $( ".director_name", el ).autocomplete( '%s', {
                mustMatch: true,
                formatItem: formatItem,
                formatResult: formatResult
            });

           $( ".director_name", el ).result( function( event, data, formatted ) {
                $( ".director_id", $(this).parent() ).val( data[0] );
            });
        }

        $('#add_%s').click( function() {
            var el = $( '%s' )
            $("#w_%s").append( el )
            // ..
            bindDirector( el )
        })

        bindDirector( $( ".row-d" ) )
    });
    </script>
    """
    
    PERSON_ID = '%s_id'
    PERSON_NAME = '%s_name'
    HTML_ROW = [
        '<div class="row-d">',
            '<span class="handle">#</span>',
            '<input type="hidden" name="%s" value="%s" class="director_id" />',
            '<input type="text" name="%s" value="%s" class="director_name" />',
            '<a href="%s" class="add-another" onclick="return showAddAnotherPopup(this);">',
            '<img src="/static/img/icon_addlink.gif" width="10" height="10" alt="[+]"/></a>',
            
            '<a class="remove_row" href="javascript:void(0)">',
            '<img src="/static/img/icon_deletelink.gif" width="10" height="10" alt="Remove Item"/> %s' % _( "remove" ),
            '</a>',
        '</div>'
    ]

    def render( self, name, value, attrs=None ):
        if value is None: 
            value = []
        
        add_url = reverse( 'add-person-manual' )

        final_attrs = self.build_attrs( attrs, name=name )
        output = [ u'<div class="directors_content" id="w_%s">' % name ]

        # add empty fields
        if len( value ) == 0:
            value = [ ('', '' ), ]
        

        for v in value:
            output.append( ''.join( self.HTML_ROW ) % ( 
                self.PERSON_ID % name, v[0],
                self.PERSON_NAME % name, v[1],
                add_url
            ) )

        output.append( u'</div><a id="add_%s" href="javascript:void(0);" class="add_director"><img src="/static/img/icon_addlink.gif" width="10" height="10" alt="[+]"/> %s</a><div style="clear:both"></div>' % ( name, _( "add director" ) ) )
        
        return mark_safe( u'\n'.join( output ) + 
                         ( self.CLIENT_CODE % ( reverse( 'person-list-ajax' ), name, 
                                               ( ''.join( self.HTML_ROW ) % ( self.PERSON_ID % name, 
                                                 '', self.PERSON_NAME % name, '', add_url ) ), name
                                              ) ) )

    def value_from_datadict( self, data, files, name ):
        result = []
        
        ids = data.getlist( self.PERSON_ID % name )
        names = data.getlist( self.PERSON_NAME % name )

        for i in range( len( ids ) ):
            result.append( ( ids[i], names[i] ) )
        return result


class ActorsWidget( widgets.Widget ):

    CLIENT_CODE = """
    <script type="text/javascript">
    $('document').ready(function () {
        function formatItem( row ) {
            return row[1];
        }
        
        function formatResult( row ) {
            return row[1];
        }
        // --- sortable
        $(".actors_content").sortable({handle : '.handle', items: '.row', axis: 'y' });

        // ---
        var bindPerson = function( el ){
            $( ".remove_row", el ).click( function() {
                $(this).parent().remove()
            })

            $( ".person_name", el ).autocomplete( '%s', {
                mustMatch: true,
                formatItem: formatItem,
                formatResult: formatResult
            });

           $( ".person_name", el ).result( function( event, data, formatted ) {
                $( ".person_id", $(this).parent() ).val( data[0] );
            });
        }

        $('#add_%s').click( function() {
            var el = $( '%s' )
            $("#w_%s").append( el )
            // ..
            bindPerson( el )
        })

        bindPerson( $( ".row" ) )
    });
    </script>
    """
    
    PERSON_ID = '%s_id'
    PERSON_NAME = '%s_name'
    PERSON_ROLE = '%s_role'
    HTML_ROW = [
        '<div class="row">',
            '<span class="handle">#</span>',
            '<input type="hidden" name="%s" value="%s" class="person_id" />',
            '<input type="text" name="%s" value="%s" class="person_name" />',
            '<a href="%s" class="add-another" onclick="return showAddAnotherPopup(this);">',
            '<img src="/static/img/icon_addlink.gif" width="10" height="10" alt="[+]"/></a>',
            '<input type="text" name="%s" value="%s" class="person_role"/>',
            
            '<a class="remove_row" href="javascript:void(0)">',
            '<img src="/static/img/icon_deletelink.gif" width="10" height="10" alt="Remove Item"/> %s' % _( "remove" ),
            '</a>',
        '</div>'
    ]

    def render( self, name, value, attrs=None ):
        if value is None: 
            value = []
        
        add_url = reverse( 'add-person-manual' )

        final_attrs = self.build_attrs( attrs, name=name )
        output = [ u'<div class="actors_content" id="w_%s">' % name ]

        # add empty fields
        if len( value ) == 0:
            value = [ ('', '', ''), ('', '', ''), ('', '', '') ]
        

        for v in value:
            output.append( ''.join( self.HTML_ROW ) % ( 
                self.PERSON_ID % name, v[0],
                self.PERSON_NAME % name, v[1],
                add_url,
                self.PERSON_ROLE % name, v[2],
            ) )

        output.append( u'</div><a id="add_%s" href="javascript:void(0);" class="add_actor"><img src="/static/img/icon_addlink.gif" width="10" height="10" alt="[+]"/> %s</a>' % ( name, _( "add actor" ) ) )
        
        return mark_safe( u'\n'.join( output ) + 
                         ( self.CLIENT_CODE % ( reverse( 'person-list-ajax' ), name, 
                                               ( ''.join( self.HTML_ROW ) % ( self.PERSON_ID % name, 
                                                 '', self.PERSON_NAME % name, '',
                                                 add_url, self.PERSON_ROLE % name, '' ) ), name
                                              ) ) )

    def value_from_datadict( self, data, files, name ):
        result = []
        
        ids = data.getlist( self.PERSON_ID % name )
        names = data.getlist( self.PERSON_NAME % name )
        roles = data.getlist( self.PERSON_ROLE % name )

        for i in range( len( ids ) ):
            result.append( ( ids[i], names[i], roles[i] ) )
        return result

class CountriesWidget( widgets.TextInput ):
    CLIENT_CODE = """
    <script type="text/javascript">
    $( function() {
        $( "#%s" ).autocomplete( '%s', {
            //mustMatch: true,
	        multiple:true,
        });
    });
    </script>
    """
    
    def render( self, name, value, attrs=None ):
        if isinstance( value, type( [] ) ):
            value = ', '.join( value )

        rendered = super( CountriesWidget, self ).render( name, value, attrs )
        
        id = 'id_%s' % name
        url = reverse( 'country-list-ajax' )

        return mark_safe( rendered + ( self.CLIENT_CODE % ( id, url ) ) )

class ImageWidget( widgets.FileInput ):
    def render(self, name, value, attrs=None):
        output = []

        output.append( super( ImageWidget, self ).render( name, value, attrs ) )
        if value and hasattr( value, "url" ):
            output.append( ( '<a target="_blank" class="image_preview" href="%s"><img src="%s" alt=[image] /></a> ' % ( value.url, value.url ) ) )

        return mark_safe( u''.join( output ) )

class PersonField( fields.Field ):
    widget = PersonWidget

    def clean( self, value ):
        try:
            return Person.objects.get( pk=int( value[0] ) )
        except:
            raise forms.ValidationError( _( 'Invalid selection' ) )

class DirectorsField( fields.Field ):
    widget = DirectorsWidget

    def clean( self, value ):
        ids, result = [], []
        for id, name in value:
            # throw exception if actor is not set
            if not id or not name:
                raise forms.ValidationError( _( "Director must be set" ) )

            # ignore empty rows
            if id and name:
                try:
                    result.append( Person.objects.get( pk=int( id ) ) )

                except:
                    raise forms.ValidationError( _( 'Invalid selection' ) )
            
                # person must by unique
                if id in ids:
                    raise forms.ValidationError( _( 'The same director can be selected only once' ) + ", " + name )
            
            ids.append( id )

        if self.required and len( result ) == 0:
            raise forms.ValidationError( _( 'This field is required' ) )
        
        return result


class ActorsField( fields.Field ):
    widget = ActorsWidget

    def clean( self, value ):
        ids, result = [], []
        for id, name, role in value:
            # throw exception if actor is not set
            if role and ( not id or not name ):
                raise forms.ValidationError( _( "Actor must be set" ) )

            # ignore empty rows
            if id and name:
                try:
                    result.append( ( Person.objects.get( pk=int( id ) ), role ) )

                except:
                    raise forms.ValidationError( _( 'Invalid selection' ) )
            
                # person must by unique
                if id in ids:
                    raise forms.ValidationError( _( 'The same actor can be selected only once' ) + ", " + name )
            
            ids.append( id )

        if self.required and len( result ) == 0:
            raise forms.ValidationError( _( 'This field is required' ) )
        
        return result


class CountriesField( fields.Field ):
    widget = CountriesWidget

    def clean( self, value ):
        result = []
        for country in value.split( ',' ):
            country = country.strip();
            if country:
                result.append( country )
        #        try:
        #            result.append( Country.objects.get( country=country ) )
        #        except Country.DoesNotExist:
        #            raise forms.ValidationError( _( 'Country does not exist ( in database )' ) )
        
        if self.required and len( result ) == 0:
            raise forms.ValidationError( _( 'This field is required' ) )
        
        return result

class ImageField( fields.Field ):
    widget = ImageWidget
