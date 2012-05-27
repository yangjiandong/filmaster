from django.utils.translation import gettext_lazy as _
from django import forms

class WallPostForm(forms.Form):
    review_text = forms.CharField(required=True, max_length=1000)
