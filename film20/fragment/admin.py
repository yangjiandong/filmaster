from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from film20.fragment.models import Fragment

class FragmentAdminForm( forms.ModelForm ):
    body = forms.CharField( required=False, widget=forms.Textarea( attrs={ 'class': 'rich-text' } ), label=_( "Body" ) )
    
    class Meta:
        model = Fragment

class FragmentAdmin( admin.ModelAdmin ):
    
    form = FragmentAdminForm

    list_display = ( 'name', 'key', 'body' )
    list_filter = ( 'name', 'key', 'body' )
    prepopulated_fields = { "key": ( "name", ) }

    class Media:
       js = [
           '/static/grappelli/tinymce/jscripts/tiny_mce/tiny_mce.js', 
           '/static/tinymce_setup.js',
       ]


admin.site.register( Fragment, FragmentAdmin )
