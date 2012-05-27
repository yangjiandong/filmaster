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
from django.db import models
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

# Create your models here.
class RegistrationModel(models.Model):
    MOVIE_MANIA_LEVEL = ((1,"1"), (2,"2"), (3,"3"), (4,"4"), (5,"5"),)
    
    OPINION_STATUS_CHOICES = (
        (0, '----------------'),
        (1, 'Dobrych recenzji'),
        (2, 'Forum na poziomie'),
        (3, 'Systemu rekomendacji'),
        (4, 'Wszystkich trzech cech'),
        (5, 'Niczego mi nie brakuje'),
    )
    
    name = models.CharField('Imię i Nazwisko.', max_length=200)
    nick = models.CharField('Nick (to będzie Twój nick w serwisie!).', max_length=200)
    email = models.EmailField('Twój adres email.')
    movie_mania_level = models.IntegerField('W jakim stopniu interesujesz się filmem?', choices=MOVIE_MANIA_LEVEL)
    opinion = models.IntegerField('Czego najbardziej brakuje Ci w serwisach filmowych, które odwiedzasz?',choices=OPINION_STATUS_CHOICES)
    comment = models.TextField('Dlaczego chcesz zostać beta-testerem filmastera?',max_length=500)
    registered_at = models.DateTimeField('Data zgłoszenia,', default=datetime.now)

    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = "Zgłoszony użytkownik"
        verbose_name_plural = "Zgłoszeni użytkownicy"

class RegistrationModelAdmin(admin.ModelAdmin):
    pass

admin.site.register(RegistrationModel, RegistrationModelAdmin)

class RegistrationEmailModel(models.Model):  
    email = models.EmailField('Twój adres email.')
    registered_at = models.DateTimeField('Data zgłoszenia,', default=datetime.now)
 
    def __unicode__(self):
        return self.email
    class Meta:
        verbose_name = "Zgłoszony email"
        verbose_name_plural = "Zgłoszone emaile"

class RegistrationEmailModelAdmin(admin.ModelAdmin):
    pass

admin.site.register(RegistrationEmailModel, RegistrationEmailModelAdmin)
