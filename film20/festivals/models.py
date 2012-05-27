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
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _

from film20.core.models import Object, Film
from django.conf import settings
from film20.userprofile.countries import CountryField
from film20.utils.db import LangQuerySet
from film20.utils import cache
from film20.core.urlresolvers import reverse as abs_reverse
from film20.utils.functional import memoize_method
from film20.showtimes.utils import day_start

import pytz
def to_local_tm(s):
    timezone = s.channel.timezone_id and pytz.timezone(s.channel.timezone_id) or pytz.utc
    t = s.get_local_time(timezone)
    return day_start(t)

from film20.showtimes.models import Channel, Screening
from film20.showtimes.showtimes_helper import BaseScreeningSet

LANGUAGE_CODE = settings.LANGUAGE_CODE

import logging
logger = logging.getLogger(__name__)
from film20 import utils

# TODO:
# * localization (common object)
# * filter out festivals from tag queries (so that the festival relation is not used
#   for figuring out related films, etc)

def _upload_image_path(instance, filename):
    return 'img/festivals/%s' % filename

class Festival(Object):
    """
        Festival object representing film festial and other events
        represented on Filmaster
    """
    STATUS_OPEN = 1
    STATUS_CLOSED = 2
    FESTIVAL_STATUS_CHOICES = (
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
    )
    parent = models.OneToOneField(Object, parent_link=True)

    # general tag for the festival (e.g. ENH)
    supertag = models.CharField(_('Super Tag'), max_length=50)
    # specific tag for festival edition (e.g. ENH10)
    tag = models.CharField(_('Tag'), max_length=50)
    # twitter hashtag
    hashtag = models.CharField(_('Hash Tag'), max_length=50, null=True, blank=True)

    # official festival name
    name = models.CharField(_('Long Name'), max_length=200)
    short_name = models.CharField(_('Short Name'), max_length=20, null=True, blank=True)

    lead = models.TextField(_('Lead'), blank=True)
    body = models.TextField(_('Body'))

    start_date = models.DateField(_('Starts on'),)
    end_date = models.DateField(_('Ends on'),)
    
    supported = models.BooleanField(default=True)

    country_code = CountryField(null=True, blank=True)

    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    # assign manager
    objects = LangQuerySet.as_manager()

    event_status = models.IntegerField(choices=FESTIVAL_STATUS_CHOICES)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    event_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    background_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    background_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    menu_header_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    menu_header_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    menu_icon_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    menu_icon_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    rate_films_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    rate_films_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    suggestions_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    suggestions_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    showtimes_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    showtimes_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    community_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    community_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)

    stream_image = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
    stream_image_lowres = models.ImageField(upload_to=_upload_image_path, null=True, blank=True)
   
    theaters = models.ManyToManyField(Channel, blank=True, null=True, limit_choices_to={'type':1})

    css = models.TextField(null=True, blank=True)

    class Meta:
        get_latest_by = 'start_date'
        ordering = ('-start_date',)

    def is_closed(self):
      return self.event_status == Festival.STATUS_CLOSED

    def __unicode__(self):
        return self.name

    def get_theaters(self):
        key = cache.Key("festival_theaters", self)
        theaters = cache.get(key)
        if theaters is None:
            from film20.tagging.models import TaggedItem
            channels = self.theaters.all()
            theaters = list(Channel.objects.theaters().filter(id__in=channels))
            cache.set(key, theaters)
        return theaters

    @classmethod
    def get_open_festivals(self):
        key = cache.Key("open_festivals")
        festivals = cache.get(key)
        if festivals is None:
            festivals = Festival.objects.filter(event_status = self.STATUS_OPEN)
            festivals = list(festivals)
            cache.set(key, festivals)
        return festivals
   
    def invalidate_cache(self):
        cache.delete(cache.Key("open_festivals"))
        cache.delete(cache.Key("festival_theaters", self))
        cache.delete(cache.Key("festival_screening_dates", self))
        cache.delete(cache.Key("festival_participants", self))
        cache.delete(cache.Key("festival_films", self))
        cache.delete(cache.Key("festival_screening_set", self))
        cache.delete(cache.Key("festival_screening_set", self, True))
        cache.delete(cache.Key("festival_screening_set", self, False))
        for date in self.get_screening_dates():
            cache.delete(cache.Key("festival_screenings", self, date))

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kw):
        instance.invalidate_cache()

    def get_films(self):
        key = cache.Key("festival_films", self)
        films = cache.get(key)
        if films is None:
            films = Film.objects.tagged(self.tag.lower())
            films = list(films[:1000])
            Film.update_ranking(films)
            cache.set(key, films)
        return films

    def get_screenings_for(self, date):
        key = cache.Key("festival_screenings", self, date)
        screenings = cache.get(key)
        if screenings is None:
            channels = self.theaters.all()
            films = Film.objects.tagged(self.tag.lower())
            screenings = Screening.objects.filter(
                    channel__in=channels, 
                    utc_time__gte=date,
                    utc_time__lt=date + timedelta(days=1),
                    film__film__in=films,
            ).order_by('utc_time')
            screenings = screenings.select_related('film', 'film__film', 'channel')
            screenings = list(screenings)
            cache.set(key, screenings)
        return screenings

    def get_screening_dates(self):
        return self.get_screening_set().get_dates()

    def get_absolute_url(self):
        return abs_reverse('show_festival', args=(self.permalink,))

    @memoize_method
    def get_screening_set(self, past=False):
        key = cache.Key("festival_screening_set", self, past)
        screening_set = cache.get(key)
        if screening_set is None:
            screening_set = FestivalScreeningSet(self, past=past)
            cache.set(key, screening_set)
        return screening_set

models.signals.post_save.connect(Festival.post_save, sender=Festival)

class FestivalScreeningSet(BaseScreeningSet):
    def __init__(self, festival, **kw):
        super(FestivalScreeningSet, self).__init__(festival.get_theaters(), **kw)
        screenings = self.get_screenings(
                festival.start_date,
                festival.end_date+timedelta(days=1),
                festival.tag)
        screenings = list(screenings.filter(channel__in=self.channel_ids))
        self._screening_ids = [s.id for s in screenings]
        self._films = self._get_films(screenings)
        self._dates = sorted(set(to_local_tm(s) for s in screenings))

    def get_screening_ids(self):
        return self._screening_ids

    def get_channels(self, id):
        film = self._films.get(id)
        _channels = film and self._film_channels(film) or ()
        
        # sort channels by first screening time
        return sorted(_channels, key = lambda c:c.screenings[0])

    def wrap_films(self, film_list):
        from film20.utils.misc import ListWrapper
        class FilmWrapper(ListWrapper):
            def wrap(s, films):
                for film in films:
                    film.set_screening_set(self)
                return films
        return FilmWrapper(film_list)

    def get_dates(self):
        return self._dates

class FestivalAdmin(admin.ModelAdmin):
    list_filter = ('country_code',)
    filter_horizontal = ('theaters',)

