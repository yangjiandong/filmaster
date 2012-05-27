from django.utils.translation import gettext_lazy as _
from django import forms

class WallForm(forms.Form):
    text = forms.CharField(required=True, max_length=1000, widget=forms.widgets.Textarea(attrs={'rows':1, 'cols':60, 'maxlength': 1000, 'placeholder': _('Write to all Filmaster users:')}), help_text=_('1000 characters max.'))

class FilmForm(WallForm):
    def __init__(self, place = None):
        super(FilmForm, self).__init__()
        # create an HTML5 placeholder attribute based on the field help_text
        for field_name in self.fields:
            field = self.fields.get(field_name)
            if field:
                if type(field.widget) == forms.widgets.Textarea:
                    field.widget.attrs["placeholder"] = _('Write something about this movie')

class PersonForm(WallForm):
    def __init__(self, place = None):
        super(PersonForm, self).__init__()
        # create an HTML5 placeholder attribute based on the field help_text
        for field_name in self.fields:
            field = self.fields.get(field_name)
            if field:
                if type(field.widget) == forms.widgets.Textarea:
                    field.widget.attrs["placeholder"] = _('Write something about this person')


# text = forms.CharField(required=True, widget=forms.widgets.Textarea({'placeholder':_('Write to all Filmaster users:')}), attrs={'rows':1, 'cols':60}, max_length=500, help_text=_('500 characters max.'))
