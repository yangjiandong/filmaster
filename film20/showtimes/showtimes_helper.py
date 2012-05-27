from django.db.models import Q, Max
from film20.utils import cache_helper as cache

from django.utils.translation import gettext_lazy as _

from hashlib import md5
from itertools import groupby
import datetime
import pytz
import re
import locale
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.shortcuts import get_object_or_404
from film20.core.models import Rating, Film, FilmRanking
from film20.filmbasket.models import BasketItem
from film20.recommendations.bot_helper import count_guessed_rate
from film20.core.film_helper import FilmHelper
from film20.utils.cache_helper import A_DAY
from .utils import get_today

from models import Country, Town, Screening, Channel, \
                UserChannel, FilmOnChannel, TYPE_CINEMA, TYPE_TV_CHANNEL

def film_from_film_on_channel(f):
    film = Film(
        title=f.title, 
        permalink="unmatched-film-%d" % f.pk, 
        image=None,
        production_country_list='',
    )
    film._directors = f.directors
    return film

def get_theaters(request):
    channels = []
    if request.user.is_authenticated():
        city = request.GET.get('city')
        town = city and get_object_or_404(Town, pk=city)
        if town:
            channels = Channel.objects.theaters().in_town(town)
        if not channels:
            channels = Channel.objects.selected_by(request.user,
                    Channel.TYPE_CINEMA)

    if not channels:
        geo = request.geo
        lat = geo.get('latitude')
        lon = geo.get('longitude')
        code = geo.get('country_code')
        if not code in settings.COUNTRIES_WITH_SHOWTIMES:
            return ()
        key = cache.Key("theaters", lat, lon, code)
        channels = cache.get(key)
        if channels is None:
            if lat and lon:
                channels = Channel.objects.theaters().filter(town__country__code=code).nearby(str(lat), str(lon))
                channels = list(channels.select_related('town'))
            if not channels:
                town = settings.COUNTRY_MAIN_CITY.get(code)
                town_name = town and town['name']
                if town_name:
                    try:
                        town = Town.objects.get(country__code=code, name=town_name)
                        channels = list(Channel.objects.theaters().in_town(town))
                    except Town.DoesNotExist, e:
                        pass
                else:
                    logger.warning("no main city for %s", town_name)
            channels = channels or ()
            cache.set(key, channels)

    if not channels:
        logger.warning("not theaters for %s, geo: %r", request.user, request.geo)
    return channels

def get_tv_channels(request):
    channels = []
    if request.user.is_authenticated():
        channels = Channel.objects.selected_by(request.user, Channel.TYPE_TV_CHANNEL)
    if not channels:
        geo = request.geo
        code = geo.get('country_code')
        if not code in settings.COUNTRIES_WITH_SHOWTIMES:
            return []
        channels = Channel.objects.default_tv(request.geo['country_code'])
    if not channels:
        logger.warning("not tv channels for %s, geo: %r", request.user, request.geo)
    return channels

def __film_key(f):
    if hasattr(f, '_score'):
        return -f._score
    f._score = f._guess_rating or f._average_score or 0
    f._score += f._rated and 50 or 100
    f._score += f._on_wishlist * 1000 - f._on_shitlist * 1000
    return -f._score

def __film_cmp(a, b):
    return cmp(__film_key(a), __film_key(b)) or locale.strcoll(a.title, b.title) or 0

def __film_title_cmp(a, b):
    return locale.strcoll(a.title, b.title)

def reverse_comparator(comparator):
    return lambda a, b: comparator(b, a)

def create_film_comparator(order_by):
    if re.match('[+-]?title', order_by or ''):
        if order_by[0] == '-':
            return reverse_comparator(__film_title_cmp)
        else:
            return __film_title_cmp
    else:
        return __film_cmp

MIN_VOTES_USER = getattr(settings, 'RECOMMENDATIONS_MIN_VOTES_USER')
COUNTRIES_SUPPORTED = getattr(settings, 'COUNTRIES_WITH_SHOWTIMES')

def fmt_date(date):
    return date.strftime("%Y%m%d%H%M%S")

def get_films_in_cinemas_by_country(country_code, number_of_films=4):
    """
        Gets list of most popular films in cinemas in given country.
        If country is not handled, returns films in the US.
    """

    FILMS_IN_CINEMAS_DAYS_AHEAD = getattr(settings,
            'FILMS_IN_CINEMAS_DAYS_AHEAD', 5)
    date = datetime.datetime.utcnow()
    end_date = date + datetime.timedelta(FILMS_IN_CINEMAS_DAYS_AHEAD)
    if country_code not in COUNTRIES_SUPPORTED:
        country_code = 'US'
    cinemas = Channel.objects.theaters().in_country(
            Country.objects.filter(code=country_code))
    if not cinemas:
        cinemas = Channel.objects.theaters().in_country(
                Country.objects.filter(code="US"))
    unique_films = FilmOnChannel.objects.filter(
            screening__channel__in=cinemas,
            screening__utc_time__gte=date,
            screening__utc_time__lte=end_date).values('film').distinct()
    query = (Q(filmranking__type = Rating.TYPE_FILM) &
             Q(filmranking__film__in = unique_films) &
             Q(filmranking__number_of_votes__gte = \
                    FilmRanking.MIN_NUM_VOTES_FILM))

    country_films = list(Film.objects.filter(query).order_by(
            "-filmranking__average_score")[:number_of_films])

    # If there are not enough films, take all
    if len(country_films) < number_of_films:
        query = (Q(filmranking__type = Rating.TYPE_FILM) &
                 Q(filmranking__film__in = unique_films))
        country_films = list(Film.objects.filter(query)[:number_of_films])

    return country_films

def get_films_in_tv_by_country(country_code, number_of_films=4):
    """
        Gets list of most popular films in tv in given country.
        If country is not handled, returns films in the US.
    """

    date_start = datetime.datetime.utcnow()
    date_end = datetime.datetime.utcnow() + datetime.timedelta(1)
    if country_code not in COUNTRIES_SUPPORTED:
        country_code = "US"
    tv_channels = Channel.objects.tv().in_country(
            Country.objects.filter(code=country_code))
    if not tv_channels:
        tv_channels  = Channel.objects.tv().in_country(
                Country.objects.filter(code="US"))
    unique_films = FilmOnChannel.objects.filter(
            screening__channel__in=tv_channels,
            screening__utc_time__gte=date_start,
            screening__utc_time__lte=date_end).values('film').distinct()

    query = (Q(filmranking__type = Rating.TYPE_FILM) &
             Q(filmranking__film__in = unique_films) &
             Q(filmranking__number_of_votes__gte = \
                    FilmRanking.MIN_NUM_VOTES_FILM))

    country_films = list(Film.objects.filter(query).order_by(
            "-filmranking__average_score")[:number_of_films])


    # If we don't have enough films, take 1 day ahead
    if len(country_films) < number_of_films:
        date_end += datetime.timedelta(3)
        unique_films = FilmOnChannel.objects.filter(
                screening__channel__in=tv_channels,
                screening__utc_time__gte=date_start,
                screening__utc_time__lte=date_end).values('film').distinct()

        query = (Q(filmranking__type = Rating.TYPE_FILM) &
                 Q(filmranking__film__in = unique_films) &
                 Q(filmranking__number_of_votes__gte = \
                        FilmRanking.MIN_NUM_VOTES_FILM))

        country_films = list(Film.objects.filter(query).order_by(
                "-filmranking__average_score")[:number_of_films])

        # If we still have nothing take all
        if len(country_films) < number_of_films:
            unique_films = FilmOnChannel.objects.filter(
                    screening__channel__in=tv_channels,
                    screening__utc_time__gte=date_start).values('film').distinct()

            query = (Q(filmranking__type = Rating.TYPE_FILM) &
                     Q(filmranking__film__in = unique_films))

            country_films = list(Film.objects.filter(query)[:number_of_films])

    return country_films

from film20.recommendations import engine as recommendations_engine

def user_recommendations(user, films, with_rated=False, order_by=None):
    film_ids = [f.id for f in films]

    if user and user.is_authenticated():
        profile = user.get_profile()
        basket = BasketItem.user_basket(user)
        rated_ids = set(Rating.get_user_ratings(user).keys())
        if profile.recommendations_status in (profile.NORMAL_RECOMMENDATIONS, profile.FAST_RECOMMENDATIONS):
            recommendations = recommendations_engine.compute_guess_score_for_films(user, film_ids)
        else:
            recommendations = {}

        for f in films:
            r = recommendations.get(f.id)
            b = basket.get(f.id)
            f._rated = f.id in rated_ids
            f._guess_rating = r or 0
            f._on_wishlist = b and b[0] and (b[0] != BasketItem.NOT_INTERESTED) or False
            f._on_shitlist = b and (b[0] == BasketItem.NOT_INTERESTED) or False
    else:
        for f in films:
            f._rated = False
            f._guess_rating = 0
            f._on_wishlist = False
            f._on_shitlist = False

    test_with_rated = lambda f: with_rated or not f._rated

    films = list(f for f in films if not f._on_shitlist and test_with_rated(f))

    comparator = create_film_comparator(order_by)
    return sorted(films, cmp=comparator)
    
from itertools import groupby, chain

class BaseScreeningSet(object):
    """
    This class represents set of films with screenings
    on on specified channels within time range,
    for example today screenings on user's tv channels.
    """

    def __init__(self, channels, past=False):
        self.channel_ids = set(c.id for c in channels)
        self.channel_order = dict((c.id, n) for (n, c) in enumerate(channels))
        self.channels = dict((c.id, c) for c in channels)
        self.past = past
        self.since = not past and (datetime.datetime.utcnow() - datetime.timedelta(seconds=settings.SHOWTIMES_PAST_SECONDS)) or None

    def get_channels(self, id):
        """
        return list of channels for specified film
        each channel have screenings attribute with list of screenings
        """
        raise NotImplementedError
    

    @classmethod
    def get_screenings(cls, date, to_date, tags=None):
        query = Screening.objects.filter(
                        utc_time__gte=date,
                        utc_time__lt=to_date)
        if tags:
            from film20.tagging.utils import parse_tag_input
            tags = parse_tag_input(tags.lower())

            query = query.filter(
                film__film__objectlocalized__LANG=settings.LANGUAGE_CODE,
                film__film__objectlocalized__tagged_items__tag__name__in=tags,
            )
        return query.order_by('utc_time').select_related('film', 'channel')
    
    @classmethod
    def _get_films(cls, screenings):
        # map of unique FilmOnChannel objects
        foc = dict((s.film._key(), s.film) for s in screenings)

        matched_ids = [f.film_id for f in foc.values() if f.film_id]

        ranking = dict((r.film_id, (r.average_score, r.number_of_votes)) 
                for r in FilmRanking.objects.filter(film__in=matched_ids, type=1))

        for r in FilmRanking.objects.filter(film__in=matched_ids, type=1):
            f = foc.get(r.film_id)
            assert f
            f._average_score = r.average_score
            f._number_of_votes = r.number_of_votes

        for s in screenings:
            film = foc.get(s.film._key())
            s.film = film
            film.add_screening(s)

        return foc
    
    def _film_channels(self, film_on_channel):
        from copy import copy
        channels = film_on_channel.get_screenings()
        ids = set(channels.keys())
        ids.intersection_update(self.channel_ids)
        for id in ids:
            screenings = [Screening(id=sid, utc_time=t) for (sid, t) in channels[id] if not self.since or t>=self.since]
            if screenings:
                c = copy(self.channels[id])
                c.screenings = screenings
                yield c

class ScreeningSet(BaseScreeningSet):

    @classmethod
    def get_town_films(cls, town_id, date, to_date, tags=None):
        extra = tags and (tags,) or ()
        key = cache.Key("showtimes_town_films", date, to_date, town_id, *extra)
        films = cache.get(key)
        if films is None:
            s = cls.get_screenings(date, to_date, tags)
            s = s.filter(channel__type=1)
            s = list(s.filter(channel__town=town_id))
            films = cls._get_films(s)
            timeout = not s and settings.SHOWTIMES_EMPTY_CACHE_TIMEOUT or None
            cache.set(key, films, timeout)
        return films

    @classmethod
    def get_country_tv_films(cls, country_id, date, to_date, tags=None):
        extra = tags and (tags,) or ()
        key = cache.Key("showtimes_country_tv_films", date, to_date, country_id, *extra)
        films = cache.get(key)
        if films is None:
            s = cls.get_screenings(date, to_date, tags)
            s = s.filter(film__film__isnull=False)
            s = s.filter(channel__type=2)
            s = s.filter(film__is_tv_series=False)
            s = list(s.filter(channel__country=country_id))
            films = cls._get_films(s)
            timeout = not s and settings.SHOWTIMES_EMPTY_CACHE_TIMEOUT or None
            cache.set(key, films, timeout)
        return films

    def __init__(self, date, channels, user=None, days=1, past=False, with_rated=False, without_unmatched=False, order_by=None, tags=None):
        # hack for postgres - we need naive datetime for __gte and __lt operators
        super(ScreeningSet, self).__init__(channels, past=past)
        
        assert date.tzinfo
        if date.tzinfo:
            date = date.astimezone(pytz.utc)
        date = date.replace(tzinfo=None)
        to_date = date + datetime.timedelta(days=days)

        self.user = user
        self.with_rated = with_rated
        self.without_unmatched = without_unmatched
        self.order_by = order_by
        
        self.theaters = filter(lambda c: c.type == 1, channels)
        self.tv_channels = filter(lambda c: c.type == 2, channels)
        town_ids = set(c.town_id for c in self.theaters)
        
        country_ids =set(c.country_id for c in self.tv_channels)
        
        self.film_sets = list(chain(
                (self.get_town_films(i, date, to_date, tags) for i in town_ids), 
                (self.get_country_tv_films(i, date, to_date, tags) for i in country_ids)))


    def _get_recommendations(self):
        self.films = set()
        film_ids = []

        for film_set in self.film_sets:
            for f in film_set.values():
                if not f in self.films and f.has_screenings(self.channel_ids, self.since):
                    self.films.add(f)
                    if f.film_id:
                        film_ids.append(f.film_id)

        if self.user and self.user.is_authenticated():
            profile = self.user.get_profile()
            basket = BasketItem.user_basket(self.user)
            rated_ids = Film._rated_film_ids(self.user)
            if profile.recommendations_status in (profile.NORMAL_RECOMMENDATIONS, profile.FAST_RECOMMENDATIONS):
                recommendations = recommendations_engine.compute_guess_score_for_films(self.user, film_ids)
            else:
                recommendations = {}

            for f in self.films:
                if not f.film_id:
                    continue
                r = recommendations.get(f.film_id)
                b = basket.get(f.film_id)
                f._rated = f.film_id in rated_ids
                f._guess_rating = r or 0
                f._on_wishlist = b and b[0] and (b[0] != BasketItem.NOT_INTERESTED) or False
                f._on_shitlist = b and (b[0] == BasketItem.NOT_INTERESTED) or False

        test_with_rated = lambda f: self.with_rated or not f._rated
        test_unmatched = lambda f: not self.without_unmatched or f.film_id

        films = list(f for f in self.films if not f._on_shitlist and test_with_rated(f) and test_unmatched(f))

        comparator = create_film_comparator(self.order_by)
        return sorted(films, cmp=comparator)

    def get_recommendations(self):
        from film20.utils.misc import ListWrapper
        class FilmWrapper(ListWrapper):
            def wrap(s, films_on_channel):
                for film_on_channel in films_on_channel:
                    film = film_on_channel.get_film()
                    film.set_screening_set(self)
                    yield film
        return FilmWrapper(self._get_recommendations())

    def get_recommendations_by_channel(self):
        films = self._get_recommendations()
        channels = set()
        for film in films:
            for channel in self.get_channels(film._key()):
                channels.add(self.channels[channel.id])
                self.channels[channel.id].add_film_screenings(film, channel.screenings)

        return sorted(channels, key=lambda c:self.channel_order.get(c.id))

    def get_channels(self, id):
        _channels = []
        for film_set in self.film_sets:
            film = film_set.get(id)
            if film:
                _channels.extend(self._film_channels(film))
        return sorted(_channels, key = lambda c:self.channel_order[c.id])

    @classmethod
    def _tagged_film_ids(cls, tags):
        key = cache.Key('tagged_films', tags)
        ids = cache.get(key)
        if ids is None:
            ids = set(Film.objects.tagged(tags).values_list('id', flat=True))
            logger.info("%s ids: %r", tags, ids)
            cache.set(key, ids)
        return ids

def get_films(*args, **kw):
    return ScreeningSet(*args, **kw).get_recommendations()

def collect_unique_films(start_date, channels, n, days, user=None):
    """
    tries to collect n unique films on channels
    starting from start_date
    """

    day = 0
    out = []
    while day<days and len(out) < n:
        _films = get_films(date=start_date + datetime.timedelta(days=day),
                channels=channels, user=user, days=1,
                without_unmatched=True)[:n + len(out)]
        _films = filter(lambda f: f not in out, _films)
        out.extend(_films)
        if len(out) > n:
            out = out[:n]
        day += 1
    return out


# 9000s = 2.5h
SHOWTIMES_PAST_SECONDS = getattr(settings, "SHOWTIMES_PAST_SECONDS", 9000)

def filter_past_screenings(screenings):
    start = datetime.datetime.utcnow() - datetime.timedelta(seconds=SHOWTIMES_PAST_SECONDS)
    from itertools import ifilter
    return ifilter(lambda s: s.utc_time>=start, screenings)

def filter_past(func):
    def wrapper(*args, **kw):
        ret = func(*args, **kw)
        past = kw.get('past', False)
        for (c, screenings) in ret:
            if not past:
                screenings = list(filter_past_screenings(screenings))
            if screenings:
                yield c, screenings
    return wrapper

from hashlib import md5
@filter_past
def film_screenings(film, date, channels=None, days=1, past=False, type=None):
    channels = channels or []
    date = date.replace(tzinfo=None)
    to_date = date + datetime.timedelta(days=days)
    key = cache.Key("film_screenings", film.pk or film.title, date, to_date, channels, type)
    screenings = cache.get(key)
    if screenings is None:
        if film.pk:
            q = Screening.objects.filter(film__film=film, utc_time__gte=date, utc_time__lt=to_date)\
                                  .order_by('channel', 'utc_time')
        else:
            q = Screening.objects.filter(film__title=film.title, utc_time__gte=date, utc_time__lt=to_date)\
                                  .order_by('channel', 'utc_time')

        q = q.filter(channel__in=channels)
        if type:
            q = q.filter(channel__type=type)
        
        q = q.select_related('film', 'film__film', 'channel')

        screenings = dict( (c, list(v)) for (c, v) in groupby(q, lambda s:s.channel) )
        if channels:
            screenings = list( (c, screenings[c]) for c in channels if c in screenings )
        else:
            channels = sorted(screenings.keys(), key=lambda c:c.name)
            screenings = list( (c, screenings[c]) for c in channels )
        cache.set(key, screenings)
    return screenings
    
from film20.core.models import Film
@filter_past
def channel_screenings(channel, date, films=None, days=1, past=False, order_by=None):
    date = date.replace(tzinfo=None)
    to_date = date + datetime.timedelta(days=days)
    key = cache.Key("channel_screenings", channel, date, to_date, films)
    screenings = cache.get(key)
    if screenings is None:
        screenings = Screening.objects.filter(channel=channel, utc_time__gte=date, utc_time__lt=to_date)\
                                      .order_by('film__film', 'film', 'utc_time')
        screenings = dict( (f, list(v)) for (f, v) in groupby(screenings, lambda s:(s.film.film or film_from_film_on_channel(s.film)) ) )
        if films is None:
            films = sorted( screenings.keys(), cmp=__film_cmp) # 
        screenings = list( (f, screenings[f]) for f in films if f in screenings)
        cache.set(key, screenings)

    comparator = _film_comparator(order_by)
    if comparator:
        _cmp= lambda a, b: comparator(a[0], b[0])
        logger.info(screenings)
        screenings = sorted(screenings, cmp=_cmp)

    return screenings

