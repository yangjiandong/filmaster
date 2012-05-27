# -!- coding: utf-8 -!-
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm, Form
from django.forms import ModelMultipleChoiceField, Field, Widget, \
    MultipleHiddenInput, ModelChoiceField, ChoiceField, RadioSelect, BooleanField, CheckboxSelectMultiple
from django.utils.safestring import mark_safe
from film20.core.models import Film
from models import FilmOnChannel, Town, TYPE_TV_CHANNEL
from django.conf import settings

from film20.utils import cache_helper as cache

class CandidatesWidget(MultipleHiddenInput):
    class Media:
        js = ('jquery.js',)
    def render(self, name, value, *args, **kw):
        out = super(CandidatesWidget, self).render(name, value, *args, **kw)
        def _film(film):
            directors = ', '.join(unicode(d) for d in film.directors.all())
            descr = u"%s (%s)"%(unicode(film), directors)
            return u"<a href='#' onclick='document.getElementById(\"id_film\").value=%d'>%s</a>"%(film.pk, descr)
        return mark_safe(out + '<div style="float:left">' + '<br />'.join(_film(Film.objects.get(pk=i)) for i in (value or ())) + '</div>')
    

class FilmOnChannelForm(ModelForm):
    class Meta:
        fields = ('key', 'title', 'year', 'directors', 'film', 'match', 'candidates', 'imdb_code')

    candidates = ModelMultipleChoiceField(Film.objects, widget=CandidatesWidget, required=False)

TYPE_CHOICES = (
  (1, u"Ulubione"),
  (2, u"Najbliższe"),
)

class CinemaFilterForm(Form):
    city = ChoiceField(required=False)

    def __init__(self, data, geo, nearby, *args, **kw):
        country_code = geo and geo.get('country_code') or ''
        #TODO - cache
        towns = Town.objects_with_cinemas.filter(country__code=country_code)
        choices = [('', _('Nearby'))] + [(t.id, t.name) for t in towns]
        super(CinemaFilterForm, self).__init__(data, *args, **kw)
        self.fields['city'].choices = choices

class SelectTownForm(Form):
    city = ChoiceField(required=False)
    def __init__(self, country_code, show_nearby, *args, **kw):
        super(SelectTownForm, self).__init__(*args, **kw)
        key = cache.Key("country_towns", country_code)
        if country_code in settings.COUNTRIES_WITH_SHOWTIMES:
            self.towns = cache.get(key)
            if not self.towns:
                self.towns = Town.objects_with_cinemas.filter(country__code=country_code)
                cache.set(key, self.towns)
        else:
            self.towns = ()
        choices = show_nearby and [('', _('Nearby'))] or []
        choices.extend((t.id, t.name) for t in self.towns)
        self.fields['city'].choices = choices
    
