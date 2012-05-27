#-!- coding: utf-8 -!-
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.conf import settings
from django.contrib.auth.models import User
from film20.utils.texts import normalized_text
from film20.config.urls import urls
from film20.import_films.models import FilmToImport
from film20.core.models import Film, Profile
from film20.notification.models import send as send_notice
from film20.utils import cache_helper as cache
from film20.utils.db import QuerySet, FieldChangeDetectorMixin, LangQuerySet
from film20.utils.functional import memoize_method
from film20.core.urlresolvers import reverse as abs_reverse
from django.core.urlresolvers import reverse
from .signals import film_rematched

from geonames import geo_distance, timezone
import pytz
import datetime
import json
import logging
logger = logging.getLogger(__name__)
from itertools import groupby

USER_CHANNELS_CACHE_TIMEOUT = 300
TOWN_CINEMAS_CACHE_TIMEOUT = 300
SCREENINGS_CACHE_TIMEOUT = 300

class Country(models.Model):
    name = models.CharField(max_length=32)
    code = models.CharField(max_length=2, unique=True)
    def __unicode__(self):
        return self.name or self.code

class TownManager(models.Manager):
    def get_query_set(self):
        qs = super(TownManager, self).get_query_set()
        return qs.filter(has_cinemas=True).order_by('name')

class Town(models.Model):
    country = models.ForeignKey(Country)
    name = models.CharField(max_length=32)
    last_fetched = models.DateTimeField(null=True, blank=True)
    has_cinemas = models.BooleanField(default=False)

    timezone_id = models.CharField(max_length=40, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

    objects_with_cinemas = TownManager()
    objects = models.Manager()
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        unique_together = ('name', 'country'),

TYPE_CINEMA = 1
TYPE_TV_CHANNEL = 2

class ChannelQuerySet(QuerySet):

    def selected_by(self, user, type=TYPE_CINEMA):
        if not user.is_authenticated():
            return ()
        profile = user.get_profile()
        if profile.country not in settings.COUNTRIES_WITH_SHOWTIMES:
            return ()
        key = cache.Key("user_channels", user)
        channels = cache.get(key)
        if channels is None:
            channels = Channel.objects.filter(selected_by=user, is_active=True, country__code=profile.country)
            channels = channels.order_by('type', 'userchannel__distance', 'name')
            channels = channels.extra(select={"distance":"showtimes_userchannel.distance"})
            channels = channels.select_related('town')
            cache.set(key, channels)
        return [c for c in channels if (c.type & type)]

    def in_town(self, town):
        key = cache.Key("town_theaters", town)
        channels = cache.get(key)
        if channels is None:
            channels = self.theaters().filter(town=town).order_by('name')
            channels = list(channels.select_related('town'))
            cache.set(key, channels)
        return channels

    def default_tv(self, country_code):
        key = cache.Key("default_tv", country_code)
        ret = cache.get(key)
        if ret is None:
            if country_code not in settings.COUNTRIES_WITH_SHOWTIMES:
                ret = ()
            else:
                ret = list(self.tv().filter(country__code=country_code, is_active=True, is_default=True))
            cache.set(key, ret)
        return ret
    
    def tv(self):
        return self.filter(type=TYPE_TV_CHANNEL)

    def theaters(self):
        return self.filter(type=TYPE_CINEMA)

    def in_country(self, country):
        return self.filter(country=country)

    def playing_film(self, film, date, country_code, days=1):
        to_date = date + datetime.timedelta(days=days)
        return self.filter(
            screening__film__film=film,
            screening__utc_time__gte=date,
            screening__utc_time__lt=to_date,
            country__code=country_code).distinct().select_related()
    
CHANNEL_TYPE_CHOICES = (
  (TYPE_CINEMA, u"Cinema"),
  (TYPE_TV_CHANNEL, u"TV Channel"),
)

class Channel(models.Model):
    TYPE_CINEMA = 1
    TYPE_TV_CHANNEL = 2

    name = models.CharField(max_length=128)
    type = models.IntegerField(choices=CHANNEL_TYPE_CHOICES)
    name_normalized = models.CharField(max_length=128)
    selected_by = models.ManyToManyField(User, related_name=u"selected_channels", through="UserChannel")
    last_screening_time = models.DateTimeField(null=True, blank=True)
    timezone_id = models.CharField(max_length=40, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    icon = models.ImageField(upload_to="channels/%Y/%b/%d", null=True, blank=True)
    
    country = models.ForeignKey(Country, null=True)

    town = models.ForeignKey(Town, null=True, blank=True)
    address = models.CharField(max_length=128, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    
    objects = ChannelQuerySet.as_manager()

    distance = 0

    class Meta:
        ordering = ('name', )
        unique_together = ('name', 'type', 'town', 'country'),

    def save(self, *args, **kw):

        assert self.type in (TYPE_CINEMA, TYPE_TV_CHANNEL)

        self.name_normalized = normalized_text(self.name)

        if self.type == self.TYPE_CINEMA:
            self.country = self.town.country
            if not self.timezone_id:
                if self.town.timezone_id:
                    self.timezone_id = self.town.timezone_id
                else:
                    if self.latitude and self.longitude:
                        self.timezone_id = timezone(self.latitude, self.longitude)['timezoneId']
                        self.town.timezone_id = self.timezone_id
                        self.town.save()
                    else:
                        logger.warning("%s without coords", unicode(self))

        return super(Channel, self).save(*args, **kw)

    def __unicode__(self):
        if self.type == self.TYPE_CINEMA:
            if not self.town or self.town.name in self.name:
                return self.name
            else:
                return "%s, %s" % (self.name, self.town.name)
        return self.name
    
    def __eq__(self, ob):
        return isinstance(ob, Channel) and (self.pk == ob.pk)
    
    def __hash__(self):
        return hash(self.pk)

    def __cmp__(self, other):
        return cmp(self.type, other.type) or cmp(self.distance, other.distance) or cmp(self.name, other.name)
    
    def add_film_screenings(self, film, screenings):
        if not hasattr(self, '_film_screenings'):
            self._film_screenings = []
        self._film_screenings.append((film, screenings))

    def get_screenings(self):
        return getattr(self, '_film_screenings', ())

    def to_cinema_date(self, time):
        from showtimes_helper import DAY_START_DELTA
        if not time.tzinfo:
            time = pytz.utc.localize(time)
        time = time.astimezone(pytz.timezone(self.town.timezone_id))
        return (time - DAY_START_DELTA).date()

class Fetcher(models.Model):
    name = models.CharField(max_length=32)
    channel = models.ForeignKey(Channel)
    cid = models.CharField(max_length=128)

    class Meta:
        unique_together = (('name', 'channel'), ('name', 'cid'))

class UserChannel(models.Model):
    channel = models.ForeignKey(Channel, related_name="userchannel")
    user = models.ForeignKey(User)
    distance = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    def save(self, *args, **kw):
        if self.distance is None and self.channel.type == TYPE_CINEMA:
            """ TODO: compute distance from user to cinema """
        return super(UserChannel, self).save(*args, **kw)

    @classmethod
    def invalidate_cache(cls, sender, instance, *args, **kw):
        try:
            cache.delete(cache.Key("user_channels", instance.user))
        except User.DoesNotExist:
            pass
    
    def __repr__(self):
        return repr(self.channel)
    
models.signals.post_delete.connect(UserChannel.invalidate_cache, sender=UserChannel)
models.signals.post_save.connect(UserChannel.invalidate_cache, sender=UserChannel)

class QueuedLocationManager(models.Manager):
    RECHECK_LOCATION_TIMEOUT = datetime.timedelta(seconds=1)
    
    def queue(self, user, nearby):
        profile = user.get_profile()
        model = self.model
        status = bool(nearby) and model.UPDATE_CINEMAS or model.FIND_CINEMAS
        try:
            ql = model.objects.get(user=user)
            if geo_distance(ql.latitude, ql.longitude, profile.latitude, profile.longitude)>=1.0:
                ql.latitude, ql.longitude = profile.latitude, profile.longitude
                ql.status = status
                ql.town = None
                ql.save()
            else:
                logger.debug('too near to last position, do nothing.')
        except model.DoesNotExist:
            ql = model(user=user, latitude=profile.latitude, longitude=profile.longitude, status=status)
            ql.save()

    def queued(self):
        return self.model.objects.filter(status__lt=5)

class QueuedLocation(models.Model):
    FIND_CINEMAS = 1
    UPDATE_CINEMAS = 2
    NOT_FOUND = 8
    FOUND = 9
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    status = models.IntegerField(default=0)
    user = models.ForeignKey(User)
    town = models.ForeignKey(Town, null=True, blank=True)

    objects = QueuedLocationManager()

    def __unicode__(self):
        return u"<QueuedLocation: %s (%s,%s): %s>" % (self.user, self.latitude, self.longitude, self.town)

def profile_pre_save(sender, instance, *args, **kw):
    lat, lng = instance.latitude, instance.longitude
    if instance.any_field_changed('latitude', 'longitude') and lat is not None and lng is not None:
        from film20.geo.utils import get_country_and_tz_by_lat_lng
        logger.debug('profile pre save')
        ret = get_country_and_tz_by_lat_lng(lat, lng)
        if ret:
            instance.country, instance.timezone_id = ret

def update_nearby_cinemas(instance, distance=30):
    nearby = ()
    UserChannel.objects.filter(user=instance.user, channel__type=TYPE_CINEMA).delete()
    if instance.latitude is not None and instance.longitude is not None and \
            instance.country in settings.COUNTRIES_WITH_SHOWTIMES:
        nearby = list(Channel.objects.theaters().nearby(instance.latitude, instance.longitude, distance))
        towns = set()
        if nearby:
            for i in nearby:
                towns.add(i.town_id)
                if len(towns)>2:
                    break
                UserChannel(channel=i, user=instance.user, distance=str(i.distance)).save()
    cache.delete(cache.Key("user_channels", instance.user))
    return nearby

def profile_post_save(sender, instance, created, *args, **kw):

    if instance.has_location() and instance.any_field_changed('latitude', 'longitude'):
        nearby = update_nearby_cinemas(instance)
        if instance.country in settings.COUNTRIES_WITH_SHOWTIMES:
            QueuedLocation.objects.queue(instance.user, nearby)

    if instance.is_field_changed('country') and instance.country:
        tv_channels = Channel.objects.selected_by(instance.user, Channel.TYPE_TV_CHANNEL)
        if not tv_channels:
            """ no tv channels for present country, set default"""
            logger.info("setting default channels")
            for c in Channel.objects.default_tv(instance.country):
                UserChannel.objects.get_or_create(user=instance.user, channel=c)

models.signals.pre_save.connect(profile_pre_save, sender=Profile)
models.signals.post_save.connect(profile_post_save, sender=Profile)

class FilmOnChannelManager(models.Manager):

    def match(self, movie, source='', save=True, key=None):
        title = movie.get('title')[0:128]
        year = movie.get('year')
        directors = sorted(movie.get('directors', ()))
        info = movie.get('info', '')[0:128]
        imdb_code = movie.get('imdb_code')
        tag = movie.get('tag')
        data = movie.get('data')

        if not key:
            key = title
            
            if directors:
                key = "%s (%s)" % (key, ', '.join(directors))
            if year:
                key = "%s [%s]" % (key, year)
            
        # TODO - add time checking, matches if not too old
        matches = self.get_query_set().filter(key=key).order_by('-created_at')
        if matches:
            return matches[0]
        
        obj = self.model(key=key,
                         title=title,
                         directors=', '.join(directors),
                         imdb_code=imdb_code,
                         year=year,
                         source=source,
                         info=info,
                         data=data,)
        obj.tag = tag
        try:
            obj.match_and_save(save=save)
        except Exception, e:
            logger.exception(e)
            logger.error("key: %r, title: %r, info: %r", key, title, info)
        return obj

UNMATCHED = 0
HAS_CANDIDATES = 1
FUZZY_MATCHED = 8
MATCHED = 9
NO_MATCH = -1

MATCH_CHOICES = (
  (UNMATCHED, u"Unmatched"),
  (HAS_CANDIDATES, u"Has candidates"),
  (FUZZY_MATCHED, u"Fuzzy-matched"),
  (MATCHED, u"Matched"),
  (NO_MATCH, u"No match"),
)

from film20.utils.db import FieldChangeDetectorMixin

class FilmOnChannel(models.Model, FieldChangeDetectorMixin):
    objects = FilmOnChannelManager()
    key = models.CharField(max_length=255)
    title = models.CharField(max_length=128)
    localized_title = models.CharField(max_length=128, blank=True, null=True)
    info = models.CharField(max_length=128, blank=True, null=True)
    year = models.IntegerField(null=True, blank=True)    
    # comma separated, sorted list of directors
    directors = models.CharField(max_length=255, blank=True, null=True)
    imdb_code = models.CharField(max_length=128, null=True, blank=True)
    film = models.ForeignKey(Film, null=True, blank=True)
    candidates = models.ManyToManyField(Film, null=True, blank=True, related_name='cinema_candidate')
    created_at = models.DateTimeField(auto_now_add=True)
    match = models.IntegerField(default=0, choices=MATCH_CHOICES)
    source = models.CharField(max_length=32, blank=True)
    is_tv_series = models.BooleanField(default=False)
    
    data = models.TextField(null=True, blank=True)
    priority = models.IntegerField(default=0, null=True, blank=True)

    _average_score = 0
    _number_of_votes = 0
    _rated = False
    _on_wishlist = False
    _on_shitlist = False
    _guess_rating = 0

    tag = None

    DETECT_CHANGE_FIELDS = ('film_id', 'data')

    def save(self, *args, **kw):
        if self.match in (UNMATCHED, HAS_CANDIDATES) and self.film:
            self.match = MATCHED
        self.is_tv_series = self.film and self.film.is_tv_series or False
        ret = super(FilmOnChannel, self).save(*args, **kw)
        if (self.has_field_changed('film_id') or self.has_field_changed('data')) and self.match == MATCHED:
            film_rematched.send(sender=self, instance=self)
            logger.info("film (re)matched")
            if self.has_field_changed('film_id'):
                ScreeningCheckIn.objects.filter(screening__film=self).update(film=self.film)
        return ret
    
    def __unicode__(self):
        return self.title

    def get_title(self):
        return self.localized_title or self.title
    
    @property
    def permalink(self):
        return self.film_id and self.film.permalink or "unmatched-film-%d" % self.pk
    
    @classmethod
    def film_to_import_postsave(cls, sender, instance, created, *args, **kw):
        if instance.is_imported:
            for m in cls.objects.filter(match=UNMATCHED, imdb_code=instance.imdb_id):
                m.match_and_save()
        
    def match_and_save(self, save=True):
        film = None
        candidates = []
        match = UNMATCHED
        
        if self.imdb_code:
            try:
                film = Film.objects.get(imdb_code=self.imdb_code)
                logger.debug("matched by imdb_code: %r", film)
                match = MATCHED
            except Film.DoesNotExist, e:
                admin = User.objects.get(username='admin')
                try:
                    to_import = FilmToImport.objects.get(imdb_id=self.imdb_code, comment='showtimes auto-import', user=admin)
                except FilmToImport.DoesNotExist:
                    to_import = FilmToImport(
                        user = admin,
                        title = self.title,
                        imdb_url = 'http://www.imdb.com/title/tt/%s/' % self.imdb_code,
                        imdb_id = self.imdb_code,
                        comment = 'showtimes auto-import',
                        status = FilmToImport.ACCEPTED,
                    )
                if to_import.status == FilmToImport.ACCEPTED:
                    to_import.is_imported = False
                    to_import.attempts = 0
                    to_import.save()
        else:
            directors = filter(bool, (d.strip() for d in (self.directors or '').split(',')))

            films = Film.objects.all()
            if self.tag:
                films = films.tagged(self.tag)
            films = films.match(self.title, directors, self.year, limit=10)

            if directors or self.tag or self.year:
                film = len(films)==1 and films[0] or None
                candidates = len(films) > 1 and films or []
                match = film and MATCHED or candidates and HAS_CANDIDATES or UNMATCHED

        self.film = film
        self.match = match
        if save:
            self.save()
            self.candidates = candidates
        return self

    def get_film(self):
        return Film.create_from_film_on_channel(self)

    def add_screening(self, screening):
        if not hasattr(self, '_screenings'):
            self._screenings = {}
        if not screening.channel_id in self._screenings:
            self._screenings[screening.channel_id] = []
        self.screening__utc_time__max = screening.utc_time
        self._screenings[screening.channel_id].append((screening.id, screening.utc_time))

    def has_screenings(self, channel_ids, since = None):
        """
        checks if film has screenings on any of specified channels
        """
        channels = getattr(self, '_screenings', {})
        ids = set(channels.keys())
        ids.intersection_update(channel_ids)
        if not since:
            return bool(ids)
        for id in ids:
            if any( t >= since for (_, t) in channels[id] ):
                return True
        return False

    def get_screenings(self):
        return getattr(self, '_screenings', {})

    def _key(self):
        return self.film_id or self.title

    def __eq__(self, obj):
        try:
            return self._key() == obj._key()
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self._key())

models.signals.post_save.connect(FilmOnChannel.film_to_import_postsave, sender=FilmToImport)

class FilmScreenings(models.Model):
    class Meta:
        abstract = True

    def __init__(self, film):
        self.film = film
        
    @property
    def channels(self):
        return [ FilmScreeningsChannel(channel=c, screenings=c.screenings) for c in self.film.channels ]

class FilmScreeningsChannel(models.Model):
    class Meta:
        abstract = True

    def __init__(self, channel, screenings):
        self.channel = channel
        self.screenings = screenings

class ChannelScreenings(models.Model):
    class Meta:
        abstract = True

    def __init__(self, channel):
        self.channel = channel

    @property
    @memoize_method
    def films(self):
        return [ ChannelScreeningsFilm(film=Film.create_from_film_on_channel(f), screenings=s) for (f, s) in self.channel.get_screenings() ]

class ChannelScreeningsFilm(models.Model):
    class Meta:
        abstract = True
    
    def __init__(self, film, screenings):
        self.film = film
        self.screenings = screenings

class Screening(models.Model):
    channel = models.ForeignKey(Channel)
    film = models.ForeignKey(FilmOnChannel)
    utc_time = models.DateTimeField(null=True, blank=True)
    info = models.CharField(max_length=64, null=True, blank=True)
    
    class Meta:
        unique_together = ('channel', 'film', 'utc_time')

    def __unicode__(self):
        if self.film_id and self.channel_id:
            return u"%s %s %s" % (self.film, self.channel, unicode(self.utc_time))
        return unicode(self.utc_time)

    def get_checked_in_users_str(self):
        return ', '.join(s.user.username for s in self.get_checkins())

    # TODO - per request cache ? now there is one memcache call per screening
    def get_checkins(self):
        date = self.utc_time.date()
        to_date = date + datetime.timedelta(days=1)
        if not hasattr(self, '_checkins'):
            cache_key = cache.Key("checkins", date, self.channel_id)
            self._checkins = cache.get(cache_key)
            if self._checkins is None:
                ss = ScreeningCheckIn.objects.filter(
                         screening__utc_time__gte=date,
                         screening__utc_time__lt=to_date).\
                     order_by('screening__id', 'created_at').select_related('screening', 'user')
                self._checkins = dict((k, list(g)) for k, g in groupby(ss, lambda s:s.screening))
                cache.set(cache_key, self._checkins)
        return self._checkins.get(self, [])
    
    def checkin_cnt(self):
        return len(self.get_checkins())

    def check_in(self, user, status=None):
        if status is None: status = ScreeningCheckIn.ACTIVE
        if self.film.film_id:
            s = self.film.film.last_check_in(user)
        else:
            s = None

        if s:
            s.screening = self
            s.film = self.film.film
            s.status = status
            s.save()
            return s
        try:
            s = ScreeningCheckIn.all_objects.get(user=user, screening=self)
            if status != s.status:
                s.status = status
                s.save()
        except ScreeningCheckIn.DoesNotExist:
            if status == ScreeningCheckIn.ACTIVE:
                s = ScreeningCheckIn.objects.create(user=user, screening=self, status=status, film=self.film.film)
        return s

    def check_in_cancel(self, user):
        return self.check_in(user, ScreeningCheckIn.CANCELED)
    
    def get_absolute_url(self):
        return abs_reverse('showtimes_screening', args=[self.id])
    
    def get_local_time(self, timezone):
        return pytz.utc.localize(self.utc_time).astimezone(timezone)

class ScreeningCheckInManager(models.Manager):
    def get_query_set(self):
        qs = super(ScreeningCheckInManager, self).get_query_set()
        return qs.filter(status=ScreeningCheckIn.ACTIVE).order_by('modified_at')

class ScreeningCheckIn(FieldChangeDetectorMixin, models.Model):
    screening = models.ForeignKey(Screening, related_name='checkins', null=True)
    film = models.ForeignKey(Film, related_name='film_checkins', null=True)
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.IntegerField(default = 1)
    number_of_comments = models.IntegerField(default=0)
        
    ACTIVE = 1
    CANCELED = 2
    
    objects = ScreeningCheckInManager()
    all_objects = models.Manager()

    DETECT_CHANGE_FIELDS = ('status', ) 

    class Meta:
        unique_together = ('screening', 'user')

    def save(self, *args, **kw):
        if self.screening:
            self.film = self.screening.film.film
        super(ScreeningCheckIn, self).save(*args, **kw)
        self.save_activity()

    def save_activity(self):
        """
            Save activity for checkin
        """
        from film20.useractivity.models import UserActivity
        
        channel = self.screening and self.screening.channel

        film_title = self.film and self.film.get_title() or \
                             self.screening and self.screening.film.title or ''

        title = u"%s %s %s" % (self.user.username, _("checked-in on"), film_title)
        
        if channel:
            title += " @ %s" % channel
        
        defaults = dict(
            LANG = settings.LANGUAGE_CODE,
            channel = channel,
            channel_name = channel and unicode(channel) or "",
            checkin_date = self.screening and self.screening.utc_time,
            user = self.user,
            username = self.user.username,
            film = self.film,
            film_title = film_title,
            title = title,

            # TODO: add slug and domain: FLM-1213

            film_permalink = self.film and self.film.permalink,
            activity_type = UserActivity.TYPE_CHECKIN,
            status = self.status,
        )
        act, created = UserActivity.objects.get_or_create(checkin = self, defaults=defaults)
        if not created:
            for (k, v) in defaults.items():
                setattr(act, k, v)
            act.save()
    
    def notify(self):
        from film20.useractivity.models import UserActivity
        profile = self.user.get_profile()
        tz = profile.timezone_id and pytz.timezone(profile.timezone_id) or pytz.utc
    
        data = {
            'checkin':self,
            'user':self.user,
            'screening':self.screening,
            'time':self.screening and self.screening.get_local_time(tz),
            'film':self.film or self.screening and self.screening.film,
            'channel':self.screening and self.screening.channel,
            'link': self.screening and self.screening.get_absolute_url() or self.film and self.film.get_absolute_url(),
            'hashtags': self.film and UserActivity.get_hashtags(self.film),
            'url': self.get_absolute_url(),
        }
        
        if self.film:
            data['picture'] = self.film.get_absolute_image_url()
        
        status = self.status == self.ACTIVE and "check_in" or "check_in_cancel"

        send_notice([self.user], "useractivity_" + status, data)
        followers = set(self.user.followers.followers())
        send_notice(followers, "showtimes_following_" + status, data)

        if self.screening:
            screening_users = User.objects.filter(screeningcheckin__screening=self.screening).exclude(id=self.user_id)
            send_notice(screening_users, "showtimes_screening_" + status, data)

            if self.screening.channel.type == TYPE_CINEMA:
                # TODO - select only user near this cinema
                near_cinema_users = set(User.objects.filter(selected_channels=self.screening.channel).exclude(id=self.user_id))
                logger.info("near users: %r", near_cinema_users)
                near_followers = near_cinema_users.intersection(followers)
                logger.info("near followers: %r", near_followers)
                send_notice(near_cinema_users, "showtimes_near_cinema_" + status, data)
                send_notice(near_followers, "showtimes_following_near_cinema_" + status, data)

    def get_absolute_url(self):
        if self.screening_id:
            return self.screening.get_absolute_url()
        return self.film.get_absolute_url()

    def get_slug(self):
        return reverse('show_checkin', args=[unicode(self.user), self.id])

    def get_comment_title(self):
        # TODO - add comment title
        return ''

    def get_related_films(self):
        if self.film:
            return self.film,

    def __repr__(self):
        return "<ScreeningCheckIn: film: %r status: %d>" % (self.film, self.status)


class EmailTemplateManager( LangQuerySet ):
    def get_template( self, type ):
        templates = self.filter( active_from__lte=datetime.datetime.now(), active_to__gte=datetime.datetime.now(), type=type )
        return templates[0] if len( templates ) else None

class EmailTemplate( models.Model ):
    DAILY  = 1;
    WEEKLY = 7;
    TYPE_CHOICES = (
        ( DAILY, _( "Daily" ) ),
        ( WEEKLY, _( "Weekly" ) ),
    )

    LANG = models.CharField( max_length=2, default=settings.LANGUAGE_CODE )
    title = models.CharField( _( "title" ), max_length=255 )
    content = models.TextField()

    type = models.IntegerField( _( "type" ), choices=TYPE_CHOICES, default=WEEKLY )
    active_from = models.DateField( _( "active from" ), default=datetime.datetime.now()  )
    active_to = models.DateField( _( "active to" ), default=datetime.datetime.now() + datetime.timedelta( days=7 ) )

    objects = EmailTemplateManager.as_manager()

    def __unicode__( self ):
        return "%s (%s - %s)" % ( self.title, self.active_from, self.active_to )

    def generate( self, ctx ):
        from django.template import Template, Context
        from django.template.loader import render_to_string
        from django.utils.translation import get_language, activate

        activate( settings.LANGUAGE_CODE )
        ctx.update({
            'USERNAME': str( ctx.get( 'user' ) ),
            'REGARDS': render_to_string( "notification/showtimes_weekly_recommendations/regards.html" ),
            'RECOMMENDATIONS': render_to_string( "notification/showtimes_weekly_recommendations/recomendations.html", ctx ),
        });

        context = Context( ctx )
        template = Template( self.content )
        return { 'title': self.title, 'content': template.render( context ) }


def checkins_clear_cache(sender, instance, **kw):
    if instance.screening and instance.screening.utc_time:
        cache.delete(cache.Key("checkins" , instance.screening.utc_time.date(), instance.screening.channel_id))

models.signals.post_save.connect(checkins_clear_cache, sender=ScreeningCheckIn)
models.signals.pre_delete.connect(checkins_clear_cache, sender=ScreeningCheckIn)

def checkin_send(sender, instance, created, **kw):
    if created or instance.is_field_changed('status'):
        instance.notify()

models.signals.post_save.connect(checkin_send, sender=ScreeningCheckIn)

def on_film_rematched(sender, instance, *args, **kw):
    if instance.source == 'netflix' and instance.film:
        instant = False
        if instance.data:
            try:
                data = json.loads(instance.data)
                instant = data.get('instant')
            except:
                pass
        if instance.film.netflix_id != instance.key or instant != instance.film.netflix_instant:
            logger.info('netflix update: %s', instance.film, extra={'bg':'red'})
            instance.film.netflix_id = instance.key
            instance.film.netflix_instant = instant
            instance.film.save()

from .signals import film_rematched
film_rematched.connect(on_film_rematched, dispatch_uid="on_film_remached_sig")

