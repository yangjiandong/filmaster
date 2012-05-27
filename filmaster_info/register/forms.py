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
#-*- coding: utf-8 -*-
from filmaster_info.register.models import *
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms.util import ErrorList
from filmaster_info.register.models import *

class RegistrationEmailForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.TextInput({'class':'newsletter-input'}), required=True)    

    class Meta:
        model = RegistrationEmailModel
        exclude = ('registered_at',)
        
class RegistrationForm(forms.ModelForm):
    movie_mania_level = forms.IntegerField(widget=forms.RadioSelect(choices=RegistrationModel.MOVIE_MANIA_LEVEL), label="W jakim stopniu interesujesz si? filmem (1 - ma?ym, 5 - du?ym)?")
    opinion = forms.IntegerField(widget=forms.Select(choices=RegistrationModel.OPINION_STATUS_CHOICES, default=6),label="Czego najbardziej brakuje Ci w serwisach filmowych, kt?re odwiedzasz?")
    
    class Meta:
        model = RegistrationModel
        exclude = ('registered_at',)
        
    def clean_name(self):
        name = self.cleaned_data['name']
        name = name.split(' ')
        if len(name) < 2:
            raise forms.ValidationError('Podaj imi? i nazwisko (oddzielone spacj?).')
        elif len(name) > 4:
            raise forms.ValidationError('Naprawd? Twoje imie sk?ada si? z ponad 4 wyraz?w?')
        else:
            return self.cleaned_data['name']
        
    def clean_nick(self):
        nick = self.cleaned_data['nick']
        nicks = RegistrationModel.objects.filter(nick=nick)
        if len(nick) < 3:
            raise forms.ValidationError('Nick powinien mie? przynajmniej 3 znaki.')
        elif len(nicks) > 0:
            raise forms.ValidationError('Podany nick zosta? ju? zarejestrowany.')
        else:
            return self.cleaned_data['nick']   
        
    def clean_email(self):
        email = self.cleaned_data['email']
        emails = RegistrationModel.objects.filter(email=email)
        if len(emails) > 0:
            raise forms.ValidationError('U?ytkownik o takim adresie email ju? si? zarejestrowa?.')
        else:
            return self.cleaned_data['email']
    def clean_opinion(self):
        opinion = self.cleaned_data['opinion']
        if opinion == 0:
            raise forms.ValidationError('Wybierz kt?r?? z opcji.')
        else:
             return self.cleaned_data['opinion']
    def clean_comment(self):
        comment = self.cleaned_data['comment']
        if len(comment) < 10:
            raise forms.ValidationError('Wysil si? nieco. Zale?y nam na informacji co sk?onilo Ci? do zg?oszenia si? na testera naszego serwisu.')
        elif len(comment) > 500:
            raise forms.ValidationError('Uzasadnienie jest za d?ugie, 500 znak?w wystarczy :-).')
        else:
            return self.cleaned_data['comment']
