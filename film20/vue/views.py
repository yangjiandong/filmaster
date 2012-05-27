from django.shortcuts import render, get_object_or_404
from django.views.decorators.cache import never_cache
from django import http
from django.conf import settings

from film20.core.views import PaginatorListView
from film20.utils import cache
from film20.core.deferred import defer
from film20.vue import helper as vue
from film20.core.models import Film

import logging
logger = logging.getLogger(__name__)

def recompute_recommendations(user):
    if user.id:
        routing_key = "%s%s.recommendations" % (settings.CELERY_QUEUE_PREFIX, settings.LANGUAGE_CODE)
        defer(vue.recompute_recommendations, user, _routing_key=routing_key)

def ajax_rated(request):
    recompute_recommendations(request.unique_user)
    return http.HttpResponse('ok')

def get_top(r):
    r = list(r[:vue.TOP_RECOMMENDATIONS_NR])
    empty = vue.TOP_RECOMMENDATIONS_NR - len(r)
    if empty > 0:
        r.extend([None] * empty)
    return r
    return r

@never_cache
def ajax_recommendations(request, kind):
    if kind == 'vue':
        meth = vue.get_vue_recommendations
        #if request.REQUEST.get('recalc'):
        #    recompute_recommendations(request.unique_user)
    else:
        meth = vue.get_all_recommendations
    mood = request.REQUEST.get("mood")
    return render(request, 'vue/recommendations.html', {
            'recommendations': get_top(meth(request.unique_user, mood)),
            'class': kind,
    })


@never_cache
def main(request):
    if request.user.is_anonymous():
        request.unique_user.make_unique('vue')

    if not 'rater_class' in request.session:
        from .rater import VueRater
        request.session['rater_class'] = VueRater
    
    vue_recommendations = vue.get_vue_recommendations(request.unique_user)
    similar_debug = getattr(vue_recommendations, 'similar_debug', ())
    all_recommendations = get_top(vue.get_all_recommendations(request.unique_user))
    vue_recommendations = get_top(vue_recommendations)
    
    vue_rater = request.session['rater_class']( request )
    rated_movies = len( vue_rater.get_rated_films() )
    movies_to_rate = 15 - rated_movies
    rating_progress = ( rated_movies * 100 ) / 15

    context = {
            'all_recommendations': all_recommendations,
            'vue_recommendations': vue_recommendations,
            'similar_debug': similar_debug,
            'moods': vue.MOODS,
            'rating_progress': rating_progress,
            'movies_to_rate': movies_to_rate,
            'rated_movies': rated_movies,
            }

    return render(request, 'vue/index.html', context)

class RecommendationsView(PaginatorListView):
    context_object_name = 'recommendations'
    
    def get_queryset(self):
        mood = self.request.GET.get("mood")
        return self.get_recommendations(mood)
    
    def get_context_data(self, **kw):
        context = super(PaginatorListView, self).get_context_data(**kw)
        context['moods'] = vue.MOODS
        return context

    def get_template_names(self):
        names = super(RecommendationsView, self).get_template_names()
        if 'ajax' in self.request.GET:
            names = ('vue/detailed_recommendations_ajax.html', )
        return names

class AllRecommendationsView(RecommendationsView):
    template_name = 'vue/detailed_recommendations_all.html'
    
    def get_recommendations(self, mood):
        return vue.get_all_recommendations(self.request.unique_user, mood)

class VueRecommendationsView(RecommendationsView):
    template_name = 'vue/detailed_recommendations_vue.html'
    
    def get_recommendations(self, mood):
        return vue.get_vue_recommendations(self.request.unique_user, mood)

detailed_recommendations_vue = never_cache(VueRecommendationsView.as_view())
detailed_recommendations_all = never_cache(AllRecommendationsView.as_view())

from film20.recommendations.forms import RecommendationVoteForm

@never_cache
def film_details(request, id):
    film = get_object_or_404(Film, id=id)
    recommendation_vote_form = RecommendationVoteForm(None, request.unique_user, film)
    return render(request, 'vue/film_details.html', {
            'film': film,
            'recommendation_vote_form': recommendation_vote_form,
        })

def process_vote(request):
    if not request.unique_user.id:
        return http.HttpResponse('error')

    form = RecommendationVoteForm(request.POST, request.unique_user)
    if form.is_valid():
        film_id = form.cleaned_data['film_id']
        kw = dict()
        
#        recommendations = vue.get_all_recommendations(request.unique_user, similar=False, limit=False)
#        v = recommendations.get_by_film_id(film_id)
#        if v is not None:
#            v = str(v)
#        kw['ratings_based_prediction'] = v
        
        recommendations = vue.get_vue_recommendations(request.unique_user, similar=False, limit=False)
        v = recommendations.get_by_film_id(film_id)
        if v is not None:
            v = str(v)
        kw['traits_based_prediction'] = v

        vote = form.save(**kw)
    else:
        return http.HttpResponse('error')
    return http.HttpResponse('ok')

