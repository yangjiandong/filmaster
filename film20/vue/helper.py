from urllib2 import urlopen
from urllib import urlencode
import json
import itertools

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from film20.recommendations import engine
from film20.utils import cache
from film20.utils.misc import ListWrapper
from film20.core.models import Film, Rating, SimilarFilm
from film20.film_features.models import FilmFeature
from film20.core import rating_helper
from film20.recommendations.models import RecommendationVote

import logging
logger=logging.getLogger(__name__)

MAX_RECOMMENDATIONS_NUMBER = 2000
MIN_POPULARITY = 10
TOP_RECOMMENDATIONS_NR = 6

def cache_key(*args):
    return cache.Key("vue", *args)

class Mood(object):
    def __init__(self, tag, name, include=(), exclude=()):
        self.tag = tag
        self.name = name
        self.include = include
        self.exclude = exclude

MOODS = (
    Mood("love", _("Warm"), include=(5, 7), exclude=(6,10,12,13,15,16)),
    Mood("action", _("Action"), include=[2,16], exclude=(5,10,13)),
    Mood("depressing", _("Dark"), include=[9,16], exclude=(10,)),
    Mood("comedy", _("Fun"), include=[14], exclude=(10,13)),
    Mood("experimental", _("Indie"), include=[6,10,13,15], exclude=()),
)

class RecommendationsWrapper(ListWrapper):

    MOODS_MAP = dict( (mood.tag, mood) for mood in MOODS )
    similar = None
    limit = None

    def get_mood_film_ids(self, tag):
        mood = tag and self.MOODS_MAP.get(tag)
        if not mood:
            return ()
        return FilmFeature.matching_film_ids(mood.include, mood.exclude)

    def force_similar(self, recommendations, ratings):
        if self.limit is not None and self.limit < TOP_RECOMMENDATIONS_NR:
            similar_cnt = self.limit - (self.limit / 2)
        else:
            similar_cnt = 3

        similar_films = get_similar_films()
        similar_scores = {}

        for film_id, r in ratings.items():
            weight = r - 5
            similar = similar_films.get(film_id, set())

            for s_id in similar:
                similar_scores[s_id] = similar_scores.get(s_id, 0) + weight

        recommended_ids = set(k for k, v in recommendations)

        similar_scores = [(id, score*10 + self.recommendations_dict.get(id, 0)) for (id, score) in similar_scores.items()]

        top_similar = sorted(similar_scores, key=lambda i:i[1], reverse=True)

        if settings.VUE_DEBUG:
            self.similar_debug = [(Film.get(id=id), score) for (id, score) in top_similar if id in recommended_ids]
            logger.info(self.similar_debug)
        else:
            self.similar_debug = []

        top_similar = [(id, self.recommendations_dict.get(id, 0)) for (id, score) in top_similar if score>=0 and id in recommended_ids]
        top_similar = top_similar[:similar_cnt]

        self.similar = set(i[0] for i in top_similar)
        recommendations = [r for r in recommendations if r[0] not in self.similar]

        if len(top_similar) < (self.limit or TOP_RECOMMENDATIONS_NR):
            # sort visible recommendations
            left = (self.limit or TOP_RECOMMENDATIONS_NR) - len(top_similar)
            top_similar.extend(recommendations[:left])
            del recommendations[:left]
            top_similar.sort(key=lambda r:r[1], reverse=True)

        top_similar.extend(recommendations)
        recommendations = top_similar

        return recommendations

    def __init__(self, recommendations, ratings, mood=None, similar=True, limit=True, exclude=()):

        self.ratings = ratings
        self.recommendations_dict = dict(recommendations)

        if limit and len(ratings) < TOP_RECOMMENDATIONS_NR:
            self.limit = len(ratings)

        recommendations = [
            (id, r) for (id, r) in recommendations if id not in ratings and id not in exclude
        ]

        if similar:
            recommendations = self.force_similar(recommendations, ratings)
        
        top = recommendations[0:20]

        if mood:
            mood_film_ids = self.get_mood_film_ids(mood)
            rec = [
                    (id, r) for (id, r) in top if id in mood_film_ids
            ]
            left = max(TOP_RECOMMENDATIONS_NR - len(rec), 0)
            # if left:
            #     r =((id, r) for (id, r) in recommendations if id in mood_film_ids and (id, r) not in rec) 
            #     rec.extend(itertools.islice(r, 0, left))
            recommendations = rec
        else:
            recommendations = top

        if self.limit is not None:
            recommendations = recommendations[:self.limit]

        super(RecommendationsWrapper, self).__init__(recommendations)

    def get_by_film_id(self, film_id):
        return self.recommendations_dict.get(film_id)

    def wrap(self, items):
        for id, rating in items:
            film = Film.get(id=id)
            film.guess_rating = rating
            film.similar = self.similar and (film.id in self.similar)
            yield film

def invalidate_mood_cache():
    for mood in MOODS:
        cache.delete(cache_key("mood_film_ids", mood.tag))

KNOWN_FILMS_NR = settings.VUE_MIN_KNOWN_FILMS_NR

def get_vue_film_ids(skip_cache=False):
    key = cache_key("vue_film_ids")
    ids = cache.get(key)
    if not skip_cache and ids is not None:
        return ids
    ids = Film.objects.tagged('vue2012').values_list('id', flat=True)
    if len(ids) < 50:
        ids = Film.objects.all().order_by('-popularity').values_list('id', flat=True)[:150]
    ids = set(ids)
    cache.set(key, ids)
    return ids

def get_similar_films(skip_cache=False):
    """
    returns dict(film_id, set(similar_films))
    """
    
    key = cache_key("similar_films")
    ret = cache.get(key)
    if not skip_cache and ret is not None:
        return ret

    q = SimilarFilm.objects.all()
    q = q.exclude(film_a__production_country_list__icontains='Poland').exclude(film_a__production_country_list__icontains='Polska')
    gr = itertools.groupby(q.order_by('film_b'), key=lambda s:s.film_b_id)
    d = dict( (id, set(f.film_a_id for f in items)) for (id, items) in gr )

    cache.set(key, d)

    return d

def get_similar_to(film_id):
    """
    return set of films similar to film_id
    returned set is subset of known_film_ids()
    """
    known = get_known_film_ids()
    similar = get_similar_films()
    
    return similar.get(film_id, set()) & known

def _filter_films(films):
    return films.filter(popularity__gte=10).\
            exclude(production_country_list__icontains='Poland').exclude(production_country_list__icontains='Polska').\
            distinct().values_list('id', flat=True).order_by('-popularity')

def get_db_similar_film_ids(film_set, known_ids=None):
    similar = _filter_films(Film.objects.filter(similar_to__in=film_set))
    return [film_id for film_id in similar if film_id not in film_set and (known_ids is None or film_id in known_ids)]

def get_known_film_ids(skip_cache=False):
    key = cache_key("known_film_ids")
    known = cache.get(key)
    if not skip_cache and known is not None:
        return known

    unknown_film_ids = get_vue_film_ids(skip_cache)

    known = set(get_db_similar_film_ids(unknown_film_ids))

    if len(known) >= KNOWN_FILMS_NR:
        if KNOWN_FILMS_NR > 0:
            known = set(list(known)[:KNOWN_FILMS_NR])
    else:
        for id in _filter_films(Film.objects.all()):
            if id not in known and id not in unknown_film_ids:
                known.add(id)
            if len(known) >= KNOWN_FILMS_NR:
                break
    cache.set(key, known, cache.AN_HOUR)
    return known

def get_most_similar_known_film_ids(vue_ids, known_ids):
    """
        returns list of tuples (film_id, similarity_to_all_vue_films), sorted by similarity (desc)
    """
    from film20.new_recommendations.rateless_alg import rec_engine
    r = rec_engine.get_recommender()
    return sorted([(k, r.calculate_total_similarity(k)) for k in known_ids], key=lambda i:i[1], reverse=True)

def get_ordered_known_film_ids():
    vue_ids = get_vue_film_ids()
    known_ids = get_known_film_ids()
    exclude_ids = list(Film.objects.tagged('sequel').values_list('id', flat=True))
    ordered = get_most_similar_known_film_ids(vue_ids, known_ids)

    threshold = ordered[0][1] * 0.01
    most_similar_ids = [film_id for (film_id, sim) in ordered if sim >= threshold] 

    db_similar_films = get_db_similar_film_ids(vue_ids, known_ids)
    db_similar_films_set = set(db_similar_films)

    # intersection of most_similar ids and db_similar_films
    top = [film_id for film_id in most_similar_ids if film_id in db_similar_films_set and film_id not in exclude_ids]

    # extend with remaing most_similar_ids
    top.extend(film_id for film_id in most_similar_ids if film_id not in db_similar_films_set and film_id not in exclude_ids)

    # extend with remaing db_similar_films
    top_set = set(top)
    top.extend(film_id for film_id in db_similar_films if film_id not in top_set and film_id not in exclude_ids)

    return top

def get_vue_recommendations(user, mood=None, similar=True, limit=True):
    from film20.new_recommendations.rateless_alg import rec_engine
    if not user.id:
        return ()
    ratings = rating_helper.get_user_ratings(user.id)
    unliked = RecommendationVote.get_unliked_film_ids(user)
    recommendations = rec_engine.get_recommendations(ratings.items(), 1000)

    key = cache.Key("user_vue_recommendations", user.id)
    cache.set(key, recommendations, cache.A_WEEK)

    return RecommendationsWrapper(recommendations, ratings, mood, similar=similar, limit=limit, exclude=unliked)

def init_vue_recommendations():
    from film20.core.models import Film
    from film20.new_recommendations.rateless_alg import rec_engine

    unknown_film_ids = get_vue_film_ids(skip_cache=True)
    known_film_ids = get_known_film_ids(skip_cache=True)
    cache.delete(cache_key("similar_films"))
    cache.delete(cache_key("known_film_ids"))
    print "known_films", len(known_film_ids)
    print "vue_films", len(unknown_film_ids)
    assert unknown_film_ids and known_film_ids
    rec_engine.do_create_similarities(known_film_ids, unknown_film_ids)

# ALL TIMES RECOMMENDATIONS

def notify_user(user, data):
    msg = json.dumps(data)
    data = urlencode(dict(
        text=msg,
        client_id=user.username,
    ))
    try:
        urlopen('http://filmaster-tools.appspot.com/send/', data).read()
    except Exception, e:
        logger.warning(e)

def recompute_recommendations(user):
    engine.compute_user_features(user, save=True)

    key = cache_key("top_film_ids", MAX_RECOMMENDATIONS_NUMBER)
    film_ids = cache.get(key)
    if film_ids is None:
        film_ids = Film.objects.filter(popularity__gte=MIN_POPULARITY)
        film_ids = film_ids.with_poster().with_description().values_list('id', flat=True)
        film_ids = film_ids.exclude(production_country_list__icontains='Poland').exclude(production_country_list__icontains='Polska')
        film_ids = film_ids.order_by('-popularity')[:MAX_RECOMMENDATIONS_NUMBER]
        film_ids = list(film_ids)
        cache.set(key, film_ids)

    recommendations = [s for s in engine.compute_guess_score_for_films(user, film_ids).items() if s[1]]
    recommendations = sorted(recommendations, key=lambda s:-s[1])

    return recommendations

def get_all_recommendations(user, mood=None, similar=True, limit=True):
    if not user.id:
        return ()

    recommendations = recompute_recommendations(user)
    ratings = rating_helper.get_user_ratings(user.id)

    return RecommendationsWrapper(recommendations, ratings, mood, similar=similar, limit=limit)

