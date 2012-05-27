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
import logging
logger = logging.getLogger(__name__)

from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.translation import gettext as _
from django.conf import settings
from django.views.generic import detail
from django.contrib.auth.models import User

from film20.core.models import Film
from film20.festivals.models import Festival, FestivalScreeningSet
from film20.showtimes.showtimes_helper import get_films
from film20.showtimes.models import Screening, ScreeningCheckIn

from film20.recommendations.views import show_tag_page
from film20.utils.utils import *
from film20.config.urls import full_url

from film20.useractivity.views import WallView
from film20.festivals.models import Festival
from film20.useractivity.models import UserActivity
from film20.tagging.models import Tag
from film20.utils import cache

from itertools import takewhile, count
import datetime
import pytz

from film20.core.views import PaginatorListView

from film20.showtimes.showtimes_helper import user_recommendations

class FestivalMixin(object):

    def get_object(self):
        festival = get_object_or_404(Festival.objects, permalink=self.kwargs['permalink'])
        self.channels = list(festival.get_theaters())
        self.days = festival.get_screening_dates()

        self.screening_set = festival.get_screening_set()

        self.all_films = self.screening_set.wrap_films(festival.get_films())
        self.all_recommended_films = user_recommendations(self.request.user, self.all_films)
        return festival

    def _filter(self, items):
        q = self.request.GET.get('q', '').lower().strip()
        if not q:
            return items
        
        def test(item):
            def search_keys():
                for s in item.title.split():
                    yield s
                for s in item.get_title().split():
                    yield s
                for d in item.get_directors():
                    yield d.get_localized_name()
                    yield d.get_localized_surname()

            return any(i.lower().startswith(q) for i in search_keys())

        return filter(test, items)

    def checked_in_users(self):
        key = cache.Key("festival_participants", self.object)
        users = cache.get(key)
        if users is None:
            from django.db.models import Min

            # fetch user checked-in on festival screenings

            users = list(User.objects.filter(is_active=True,
                    screeningcheckin__screening__in=self.screening_set.get_screening_ids()
            ).annotate(Min('screeningcheckin__created_at')))
            for u in users:
                u.activity_date = u.screeningcheckin__created_at__min

            users = dict( (u.id, u) for u in users )

            # add users with activities tagged with festival tag
            users2 = User.objects.filter(is_active=True,
                user_activity__tagged_items__tag__name=self.object.tag.lower(),
                user_activity__LANG=settings.LANGUAGE_CODE,
                user_activity__created_at__gte=self.object.start_date,
                user_activity__created_at__lt=self.object.end_date + datetime.timedelta(days=1),
                profile__metacritic_name='',
            ).annotate(Min('user_activity__created_at'))

            for u in users2:
                u.activity_date = u.user_activity__created_at__min

                if not u.id in users or u.activity_date < users[u.id].activity_date:
                    users[u.id] = u

            users = sorted(users.values(), key=lambda u:u.activity_date)
            cache.set(key, users)
        return users

    def get_context_data(self, **kw):
        today = datetime.datetime.utcnow().date()
        context = super(FestivalMixin, self).get_context_data(**kw)
        f = self.object
        context['festival'] = f
        context['festival_days'] = self.days
        context['checked_in_users'] = self.checked_in_users()
        context['is_past'] = self.object.end_date and self.object.end_date < today
        context['query_string'] = self.request.GET.get('q', '')
        context['filter'] = {
            'date':self.days and self.days[0],
            'days':len(self.days),
            'channels':self.channels,
        }
        context['today_screenings'] = self.object.get_screenings_for(today)
        context['all_recommended_films'] = self.all_recommended_films
        return context
    
class FestivalView(FestivalMixin, WallView):
    template_name = 'festivals/festival.html'

    def get_activities(self):
        return UserActivity.objects.tagged(self.object.tag)

    def create_wallpost(self, text, **extra):
        extra['tags'] = ', '.join((_('festival'), self.object.supertag, self.object.tag))
        return super(FestivalView, self).create_wallpost(text, **extra)

show_festival = FestivalView.as_view()

class FestivalListView(FestivalMixin, PaginatorListView):
    subtitle = None

    def get(self, *args, **kw):
        self.object = self.get_object()
        return super(FestivalListView, self).get(*args, **kw)
    
    def get_context_data(self, **kw):
        context = super(FestivalListView, self).get_context_data(**kw)
        context['subtitle'] = self.subtitle
        context['by_original_title'] = self.kwargs.get('order_by') == 'original_title'
        return context

class FestivalRecommendations(FestivalListView):
    template_name = 'festivals/films.html'
    page_size = 10
    subtitle = _("Recommendations")

    def get_queryset(self):
        return self._filter(self.all_recommended_films)

festival_recommendations = FestivalRecommendations.as_view()

class FestivalAgenda(FestivalListView):
    template_name = 'festivals/agenda.html'
    page_size = 20
    
    def get_context_data(self, **kw):
        context = super(FestivalAgenda, self).get_context_data(**kw)
        context['date'] = self.date
        return context

    def get_queryset(self):
        date = self.kwargs.get('date')
        self.date = datetime.datetime.strptime(date, "%Y-%m-%d")
        return self.object.get_screenings_for(self.date)

festival_agenda = FestivalAgenda.as_view()

class FestivalFilms(FestivalListView):
    template_name = 'festivals/films.html'
    page_size = 10
    subtitle = _("films")

    def get_queryset(self):
        if self.kwargs.get('order_by') == 'original_title':
            key = lambda f:f.title
        else:
            key = lambda f:f.get_title()
        return sorted(self._filter(self.all_films), key=key)

festival_films = FestivalFilms.as_view()

class FestivalReviews(FestivalListView):
    template_name = 'festivals/reviews.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        return UserActivity.objects.all_notes().tagged(self.object.tag).select_related('film')

festival_reviews = FestivalReviews.as_view()

from film20.recommendations.views import RankingMixin
class FestivalRanking(RankingMixin, FestivalListView):
    festival = True
    template_name = "festivals/ranking.html"
    page_size = 20
    
    subtitle = _("ranking")

    def get_genre(self):
        return self.object.tag

festival_ranking = FestivalRanking.as_view()

