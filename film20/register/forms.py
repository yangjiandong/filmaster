from django import forms
from django.utils.translation import gettext_lazy as _
from film20.register.models import RegistrationModel

class RegistrationForm(forms.ModelForm):
    opinion = forms.IntegerField(widget=forms.RadioSelect(choices=RegistrationModel.STATUS_CHOICES), label=_('On which platform would you like to run Filmaster Mobile?'))

    class Meta:
        model = RegistrationModel
        exclude = ('created_at','user', 'LANG')