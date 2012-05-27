from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.contrib import messages

from models import Screening, Channel, TYPE_CINEMA
from urllib import urlencode
import pytz
import datetime, logging
logger = logging.getLogger(__name__)

from forms import *

from showtimes_helper import get_films, get_theaters, get_tv_channels
from .utils import get_today, get_date, get_available_showtime_dates, parse_date
from urllib import urlencode
from film20.core.urlresolvers import reverse as abs_reverse, make_absolute_url

dtime = datetime.datetime

from forms import SelectTownForm

def check_location(view):
    def _check(request, *args, **kw):
        if request.user.is_authenticated() and not 'ajax' in request.GET:
            profile = request.user.get_profile()
            url = abs_reverse('edit_location') + '?' + urlencode({'next':make_absolute_url(request.path_info)})
            if not profile.has_location():
                messages.add_message(request, messages.WARNING, _("Your location is not set. Change it <a href='%s'>here</a>.") % url)
            elif profile.location_changed(request.geo):
                messages.add_message(request, messages.INFO, _("Your location may be inaccurate. Check <a href='%s'>settings</a>.") % url)
        return view(request, *args, **kw) 
    return _check

from film20.core.views import PaginatorListView

class Showtimes(PaginatorListView):
    template_name = "showtimes/films.html"
    context_object_name = 'films'
    page_size = 10

    def get(self, *args, **kw):
        self.date = get_date(self.request)
        self.past = 'past' in self.request.GET
        self.with_rated = 'with_rated' in self.request.GET
        self.order_by = self.request.GET.get('order')
        self.channels = get_theaters(self.request)

        return super(Showtimes, self).get(*args, **kw)

    def get_queryset(self):
        return get_films(self.date, self.channels, self.request.user, past=self.past, with_rated=self.with_rated, order_by=self.order_by)

    def get_context_data(self, *args, **kw):
        city = self.request.GET.get('city')
        town = city and get_object_or_404(Town, pk=city)
        country_code = self.channels and self.channels[0].town.country.code or None

        city_form = SelectTownForm(country_code, True, initial={
            'city':town and town.pk or '',
        })

        ctx = dict(
            city_form=city_form,
            theaters=self.channels,
            days=get_available_showtime_dates(self.request),
            date=self.date,
        )
        context = super(Showtimes, self).get_context_data(*args, **kw)
        context.update(ctx)
        return context

showtimes = check_location(Showtimes.as_view())

TV_FILMS_PER_DAY = 6

@check_location
def showtimes_tv(request, by_film=True, type=Channel.TYPE_CINEMA):
    today = get_today(request.timezone)

    channels = get_tv_channels(request)

    past = 'past' in request.GET
    with_rated = 'with_rated' in request.GET

    days = []
    all_films = []

    for day in (0, 1, 2):
        date = today + datetime.timedelta(days=day)
        films = get_films(date, channels, request.user, without_unmatched=True, past=past, with_rated=with_rated)[:TV_FILMS_PER_DAY + 1]
        has_more = len(films) > TV_FILMS_PER_DAY
        films = films[:TV_FILMS_PER_DAY]
        if films:
            days.append({'date':date, 'films':films, 'has_more':has_more})
            all_films.extend(films)
            
    
    ctx = dict(
        days=days,
        films=all_films,
    )

    return render(request, "showtimes/films_tv.html", ctx)

@check_location
def showtimes_tv_single_day(request, date):
    channels = get_tv_channels(request)

    past = 'past' in request.GET
    with_rated = 'with_rated' in request.GET
    
    date = parse_date(request, date)

    films = get_films(date, channels, request.user, without_unmatched=True, past=past, with_rated=with_rated)
    
    ctx = dict(
        date=date,
        films=films,
    )

    if not 'ajax' in request.GET:
        template = 'showtimes/films_tv_single_day.html'
    else:
        template = 'showtimes/films_tv_single_day_ajax.html'

    return render(request, template, ctx)


def theater(request, id):
    channel = get_object_or_404(Channel, id=id, type=Channel.TYPE_CINEMA)
    channels = [channel]

    city = request.GET.get('city')
    town = city and get_object_or_404(Town, pk=city)
    
    if town:
        theaters = Channel.objects.in_town(town)
    else:
        theaters = get_theaters(request)

    country_code = channel.town.country.code
    
    form = SelectTownForm(country_code, True, initial={
        'city':town and town.pk or '',
    })

    date = get_date(request)

    past = 'past' in request.GET
    films = get_films(date, channels, request.user, past=past)

    return render(request, "showtimes/theater.html", {
        'city_form':form,
        'town':town,
        'theaters':theaters,
        'channel':channel,
        'date':date,
        'films': films,
        'days':get_available_showtime_dates(request),
    })

def tvchannel(request, id):
    channel = get_object_or_404(Channel, pk=id)
    if channel.type == Channel.TYPE_CINEMA:
        return HttpResponseRedirect(abs_reverse(theater, args=[id]))
    assert channel.type == Channel.TYPE_TV_CHANNEL
    channels = [channel]

    date = get_date(request)
    past = 'past' in request.GET
    films = get_films(date, channels, request.user, past=past, without_unmatched=True)
    ctx = dict(
        channel=channel,
        date=date,
        days=get_available_showtime_dates(request),
        films=films,
    )
    return render(request, "showtimes/single_channel.html", ctx)

def screening(request, id):
    screening = get_object_or_404(Screening, pk=id)
    
    if screening.channel.type == screening.channel.TYPE_CINEMA:
        town = screening.channel.town
        form = SelectTownForm(town.country.code, True, initial={
            'city':town.pk,
        })
        theaters = Channel.objects.in_town(town)
    else:
        form = None
        theaters = ()

    ctx = dict(
        screening=screening, 
        channel=screening.channel,
        screenings=[screening],
        theaters=theaters,
        city_form=form,
        film=screening.film.get_film(),
        films=screening.film.film and [screening.film.film] or [],
    )
    return render(request, "showtimes/single_screening.html", ctx)

from film20.useractivity.views import WallView
from film20.useractivity.models import UserActivity

class ScreeningView(WallView):
    template_name = "showtimes/single_screening.html"
    post_form = False

    def get_object(self):
        return get_object_or_404(Screening, pk=self.kwargs['id'])
    
    def get_activities(self):
        return UserActivity.objects.filter(checkin__screening=self.object)

    def get_context_data(self, **kw):
        context = super(ScreeningView, self).get_context_data(**kw)
        screening = self.object
        if screening.channel.type == screening.channel.TYPE_CINEMA:
            town = screening.channel.town
            form = SelectTownForm(town.country.code, True, initial={
                'city':town.pk,
            })
            theaters = Channel.objects.in_town(town)
        else:
            form = None
            theaters = ()

        context.update(dict(
            screening=screening, 
            channel=screening.channel,
            screenings=[screening],
            theaters=theaters,
            city_form=form,
            film=screening.film.get_film(),
            films=screening.film.film and [screening.film.film] or [],
        ))
        return context

screening = ScreeningView.as_view()
