from datetime import datetime

from django.utils.translation import gettext as _
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from film20.showtimes.models import FilmOnChannel, Channel, \
        UserChannel, TYPE_CINEMA, TYPE_TV_CHANNEL
from film20.showtimes import showtimes_helper
from film20.showtimes.utils import get_today

from film20.showtimes.views import theater as theater_view, tvchannel as tvchannel_view
from film20.core.urlresolvers import reverse
from film20.utils import cache_helper as cache
import datetime
import re
import pytz

import logging
logger = logging.getLogger(__name__)

from film20.utils.template import Library
register = Library()

WEEKDAYS = [_("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), _("Saturday"), _("Sunday")]

@register.simple_tag
def channelurl(channel):
    if channel.type == TYPE_CINEMA:
        return reverse(theater_view, args=[channel.pk])
    elif channel.type == TYPE_TV_CHANNEL:
        return reverse(tvchannel_view, args=[channel.pk])
    else:
        return '#'

@register.filter
def film_channels(screenings, film):
    return screenings.film_channels(film)

@register.filter
def channel_films(screenings, channel):
    return screenings.channel_films(channel)

@register.filter
def film_screenings(film, filter):
    past = filter.get('past', False)
    screenings = showtimes_helper.film_screenings(film, filter['date'], filter['channels'], past=past, days=filter.get('days', 1))
    # TODO
    return [s for i, s in enumerate(screenings) if i<10]


@register.filter
def channel_screenings(channel, filter):
    past = filter.get('past', False)
    order_by = filter.get('order_by')
    return showtimes_helper.channel_screenings(channel, filter['date'], filter.get('films'), past=past, order_by=order_by)

@register.inclusion_tag('showtimes/notification/filmscreenings.txt')
def filmscreenings_text(user, film, channels, date, days):
    screenings = list(showtimes_helper.film_screenings(film, date, channels, days=days))
    timezone_id = user.get_profile().timezone_id
    try:
        timezone = timezone_id and pytz.timezone(timezone_id) or pytz.utc
    except pytz.UnknownTimeZoneError:
        timezone = pytz.utc
    
    return dict(
        film=film,
        channels=channels,
        date=date,
        days=days,
        screenings=screenings,
        timezone=timezone,
    )

def _fmt_time_html(time):
    return mark_safe(u"%d<sup>%02d</sup>" % (time.timetuple()[3:5]))

def _fmt_time_txt(time):
    return mark_safe(u"%d:%02d" % (time.timetuple()[3:5]))

def to_local_time(tm, timezone):
    if not tm.tzinfo:
        tm = pytz.utc.localize(tm)
    return tm.astimezone(timezone)
register.filter(to_local_time)

@register.filter
def local_time(screening, timezone):
    return screening.get_local_time(timezone)

@register.filter
def local_time_html(screening, timezone):
    return _fmt_time_html(screening.get_local_time(timezone))

@register.filter
def local_time_txt(screening, timezone):
    return _fmt_time_txt(screening.get_local_time(timezone))

fmt_time_html = register.filter(_fmt_time_html)

BR_RE=re.compile("\r?\n\s*", re.M)

@register.filter
def striplinebreaks(txt):
    return BR_RE.sub("", txt).strip()

BR2_RE=re.compile("(\r?\n){2,}", re.M)
@register.filter
def stripextralinebreaks(txt):
    return BR2_RE.sub("\n\n", txt).strip()

TODAY_TOMORROW = _("Today"), _("Tomorrow"), _("The day after tomorrow")

@register.simple_tag(takes_context=True)
def pretty_weekday(context, date):
    from ..views import get_today
    timezone = context['request'].timezone
    days = (date - get_today(timezone)).days
    
    if days < 3:
        return TODAY_TOMORROW[days]

    return to_local_time(date, timezone).strftime("%A")

@register.simple_tag(takes_context=True)
def screening_weekday(context, screening):
    timezone = context['request'].timezone
    return WEEKDAYS[screening.get_local_time(timezone).weekday()]

@register.inclusion_tag('aside/showtimes.html', takes_context=True)
def showtimes_menu(context):
    request = context['request']
    channel = context.get('channel')
    return {
            'menu_channels': showtimes_helper.get_tv_channels(request),
            'channel': channel,
            }

@register.widget('dashboard/top_personalized_recommendations.html')
def top_personalized_recommendations(request):
    user = request.user
    has_location = user.is_authenticated() and user.get_profile().has_location()
    
    cinema_films = []
    tv_films = []
    
    today = get_today(request.timezone)
    a_day = datetime.timedelta(days=1)

    key = cache.Key("top_personalized_recommendations", today, request.user)

    films = cache.get(key)
    if films is None:
        cinemas = showtimes_helper.get_theaters(request)
        tvs = showtimes_helper.get_tv_channels(request)

        # How many days ahead we want to check
        PERSONALIZED_CINEMA_DAYS = settings.PERSONALIZED_CINEMA_DAYS
        PERSONALIZED_TV_DAYS = settings.PERSONALIZED_TV_DAYS
        # How many films we want to get
        PERS_CINEMA_NUMBER = settings.PERSONALIZED_CINEMA_FILMS_NUMBER
        PERS_TV_NUMBER = settings.PERSONALIZED_TV_FILMS_NUMBER

        # We get films sorted by personal taste of user
        if cinemas:
            cinema_films = showtimes_helper.collect_unique_films(
                    today, cinemas, PERS_CINEMA_NUMBER, 
                    settings.PERSONALIZED_CINEMA_DAYS, user=user)

        if tvs:
            tv_films = showtimes_helper.collect_unique_films(
                    today, tvs, PERS_TV_NUMBER, 
                    settings.PERSONALIZED_TV_DAYS, user=user)
        
        films = (cinema_films, tv_films)
        cache.set(key, films)
    
    (cinema_films, tv_films) = films

    display = (not has_location) | bool(tv_films) | bool(cinema_films)

    return {
        'display': display,
        'has_location': has_location,
        'tv_films': tv_films,
        'cinema_films': cinema_films,
    }

@register.filter
def to_checkin_activity_message( date, created_at ):
    dd = date - created_at
    seconds = ( dd.microseconds + ( dd.seconds + dd.days * 24 * 3600 ) * 10**6 ) / 10**6

    if seconds > 0:
        return _( "is planing to watch" )

    if seconds <= 0 and seconds >= -7200:
        return _( "is watching" )

    return _( "watched" )
