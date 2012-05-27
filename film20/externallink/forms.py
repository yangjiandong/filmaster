from django.utils.translation import ugettext as _
from django import forms

from film20.core.models import Trailer
from film20.externallink.models import *


class ExternalLinkForm(forms.ModelForm):
    LINK_CHOICES = (
        (ExternalLink.REVIEW, _('Review')),
        (ExternalLink.NEWS, _('News')),
        (ExternalLink.BOOK, _('Book')),)
    title = forms.CharField(required=True)
    url_kind = forms.IntegerField(widget=forms.Select(choices=LINK_CHOICES))
    excerpt = forms.CharField(required=True,max_length=200,widget=forms.Textarea(attrs={'rows':'10','cols':'34'}))

    class Meta:
        model = ExternalLink
        exclude = ('film','person','user','created_at','updated_at','is_deleted','LANG','type',
                   'version','permalink','status','video_thumb','title')

class ExternalVideoForm(forms.ModelForm):

    class Meta:
        model = ExternalLink
        exclude = ('title','film','person','user','created_at','updated_at',
                   'is_deleted','LANG','type','version','permalink','status','excerpt','video_thumb', 
                    'number_of_comments', 'moderation_status', 'url_kind' )
    
    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        exclude.remove( 'film' )
        exclude.remove( 'LANG' )

        try:
            self.instance.validate_unique( exclude=exclude )
        except forms.ValidationError, e:
            self._update_errors(e.message_dict)

class TrailerForm( forms.ModelForm ):
    in_all_languages = forms.BooleanField( required = False )

    class Meta:
        model = Trailer
        fields = ( 'url', 'is_main' )

    def __init__( self, *args, **kwargs ):
        super( TrailerForm, self ).__init__( *args, **kwargs )
        self.fields['url'].label = _( "Provide video URL" )

    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        exclude.remove( 'object' )
        exclude.remove( 'LANG' )

        try:
            self.instance.validate_unique( exclude=exclude )
        except forms.ValidationError, e:
            self._update_errors(e.message_dict)


