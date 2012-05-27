from django import forms
from django.utils.translation import gettext_lazy as _

from film20.demots.models import Demot
from film20.upload.models import UserUploadedImage


class BaseAddDemotForm( forms.ModelForm ):
    line1 = forms.CharField( label=_( "type something funny here" ) )
    line2 = forms.CharField( label=_( "and here [optional]" ), required = False )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop( 'user', None )
        super( BaseAddDemotForm, self ).__init__( *args, **kwargs )

    def clean( self ):
        data = self.cleaned_data
        if self.user is not None and data.has_key( 'line1' ) and data.has_key( 'line2' ):
            try:
                Demot.objects.get( user=self.user, line1=data['line1'], line2=data['line2'] )
                raise forms.ValidationError( _( 'You already added an identical demot...' ) )
            except Demot.DoesNotExist:
                pass
        return self.cleaned_data


class AddDemotForm( BaseAddDemotForm ):

    class Meta:
        model = Demot
        fields = ( 'line1', 'line2', 'image', 'image_url' )

    def clean(self):
        data = super( AddDemotForm, self ).clean()
        if not data['image'] and not data['image_url']:
            raise forms.ValidationError( _( 'You must select one option' ) )
        return self.cleaned_data


class AddBasedOnDemotForm( BaseAddDemotForm ):
    based_on = forms.IntegerField( widget=forms.HiddenInput(), label='' )
    image = forms.IntegerField( widget=forms.HiddenInput(), required=False, label='' )

    class Meta:
        model = Demot
        fields = ( 'line1', 'line2', 'based_on', 'image' )

    def clean_based_on( self ):
        based_on = self.cleaned_data['based_on']
        try:
            return Demot.objects.get( pk=based_on )
        except Demot.DoesNotExist:
            raise forms.ValidationError( _( 'Something goes wrong, please try again later' ) )

    def clean(self):
        data = super( AddBasedOnDemotForm, self ).clean()
        data['image'] = data['based_on'].image
        return data


class AddDemotAjaxForm( BaseAddDemotForm ):
    image = forms.IntegerField( widget=forms.HiddenInput() )
    
    class Meta:
        model = Demot
        fields = ( 'line1', 'line2', 'image' )

    def clean_image( self ):
        image = self.cleaned_data['image']
        try:
            return UserUploadedImage.objects.get( pk=image ).image
        except UserUploadedImage.DoesNotExist:
            raise ValidationError( _( 'Select demot image' ) )
