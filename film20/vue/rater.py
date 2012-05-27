import random
import logging
logger = logging.getLogger(__name__)

from django.conf import settings

from film20.core import rating_helper
from film20.core.models import Film
from film20.vue import helper as vue
from film20.utils import cache

class __VueRater(rating_helper.BaseBasketsRater):

    MIN_RATE_FOR_SPECIAL_BASKET = 5

    def cache_key(self, prefix, *args, **kw):
        return cache.Key(prefix, self.__class__.__name__, 'v2', *args, **kw)

    def get_films_to_rate(self, number_of_films=1, tag=None):
        films = super(VueRater, self).get_films_to_rate(number_of_films, tag)
        if len(films) < number_of_films:
            standard_rater = rating_helper.BasketsRater(self.request)
            films.extend(standard_rater.get_films_to_rate(number_of_films - len(films), tag))
            rating_helper.set_rater(self.request, rating_helper.BasketsRater)
        return films

    def get_films(self):
        known_ids = vue.get_known_film_ids()
        return Film.objects.filter(id__in=known_ids)

    def get_related_film_ids(self, film_id):
        related_films = vue.get_similar_to(film_id)
        known = vue.get_known_film_ids()
        ret = set(related_films) & set(known)
        return ret

class VueRater(rating_helper.BaseRater):
    SHUFFLE_BLOCK_SIZE = settings.VUE_RATER_SHUFFLE_BLOCK_SIZE

    def rate_film(self, film_id, rating, type=1):
        return rating_helper.rate(self.user, rating, film_id=film_id, type=type, redis_only=False)

    def get_rated_films(self):
        return set(rating_helper.get_user_ratings(self.user.id).keys())

    def get_excluded_films(self):
        ids = set()
        ids.update(self.get_seen_films())
        ids.update(self.get_rated_films())
        return ids

    def get_films_to_rate(self, number_of_films=1, tag=None):
        key = cache.Key("vue_rater_user_films", self.user)
        user_films = cache.get(key)
        if user_films is None:
            user_films = vue.get_ordered_known_film_ids()
            if self.SHUFFLE_BLOCK_SIZE:
                shuffled = []
                while user_films:
                    block = user_films[:self.SHUFFLE_BLOCK_SIZE]
                    user_films = user_films[self.SHUFFLE_BLOCK_SIZE:]
                    random.shuffle(block)
                    shuffled.extend(block)
                user_films = shuffled
            cache.set(key, user_films)

        excluded = self.get_excluded_films()

        out = []
        for film_id in user_films:
            if film_id not in excluded:
                out.append(film_id)
            if len(out) >= number_of_films:
                break
        out = [Film.get(id=id) for id in out]
        return out

