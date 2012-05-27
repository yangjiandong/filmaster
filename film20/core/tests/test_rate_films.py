import logging;
logger = logging.getLogger(__name__)

from film20.utils.test import TestCase
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.test.client import Client, RequestFactory

from film20.core.models import Film, FilmRanking, Rating, Profile, UserRatingTimeRange
from film20.useractivity.models import UserActivity

from film20.core.rating_helper import BasketsRater
from film20.core import rating_helper
from film20.filmbasket.models import BasketItem
from django.utils import unittest

class RateFilmsTestCase(TestCase):
    fixtures = ['test_films.json']
    def setUp(self):
        logger.info("setting up few films")
        self.film_pos = {}

        from itertools import cycle
        tag = cycle(settings.BASKETS_TAGS_LIST)

        for i in range(100):
            film = Film.objects.create(
                permalink="test-film-%d" % i,
                title="title %2d" % i,
                type=Film.TYPE_FILM,
                release_year=2000,
            )
            film.save_tags(tag.next())
            self.film_pos[film.id] = i+1
            FilmRanking.objects.create(
                    film=film,
                    average_score=str((99 - i) / 10.0),
                    number_of_votes=99-i,
                    type=1,
            )
        self.user = User.objects.create_user("test", "test@test.com", "testpasswd")
        self.client = Client()
        self.client.login(username='test', password='testpasswd')

    def test_get_user_seen_films(self):
        """ Tests storing rated and seen films in cache. """

        films = Film.objects.all()
        API_VERSION = "1.1"
        username = self.user.username
        put_url = "/api/" + API_VERSION + "/user/" + username + "/ratings/film/"

        # We rate movies and check if they were added to seen_films
        for film in films[:10]:
            film_put_url = put_url + film.permalink + "/" + str(Rating.TYPE_FILM) + "/"
            self.client.put(film_put_url, {'rating': 2})
            # We check if the film was added to user_seen_films
            seen_films = Film.get_user_seen_films(self.user)
            self.assertTrue(film.id in seen_films)

        # We mark movies as seen and check if they were added to seen_films
        for film in films[10:20]:
            film.mark_as_seen(self.user)
            # We check if the film was added to user_seen_films
            seen_films = Film.get_user_seen_films(self.user)
            self.assertTrue(film.id in seen_films)

    def test_rate_films2(self):

        TAGS_LIST = settings.BASKETS_TAGS_LIST
        settings.RATE_BASKET_SIZE = len(TAGS_LIST)
        API_VERSION = "1.1"
        username = self.user.username
        put_url = "/api/" + API_VERSION + "/user/" + username + "/ratings/film/"

        # tag films
        films = Film.objects.all()
        tag_index = 0
        tags_number = len(TAGS_LIST)
        # one film has all the tags
        for tag in TAGS_LIST:
            films[0].save_tags(tag)

        for film in films[1:]:
            film.save_tags(TAGS_LIST[tag_index])
            tag_index = (tag_index + 1) % tags_number

        request = RequestFactory().get('/')
        request.user = self.user
        request.unique_user = self.user

        rater = rating_helper.get_rater(request)

        seen_films = set()
        while True:
            films_to_rate = rater.get_films_to_rate(6)
            if films_to_rate:
                for film in films_to_rate:
                    self.assertTrue(film not in seen_films)
                    rater.rate_film(film.id, 10)
                seen_films.update(films_to_rate)
            else:
                break

        self.assertEquals(len(seen_films), Film.objects.count())

    def test_rate_films(self):
        cache.set('test', True)
        self.assertTrue(cache.get('test'))
        
        cache.clear()
        self.assertTrue(cache.get('test') is None)

        settings.RATING_BASKET_SIZE = 20
        
        all_films = set()

        films = Film.get_films_to_rate(self.user, 20)
        all_films.update(f.id for f in films)
        logger.info("film ids: %r", [f.id for f in films])
        self.assertTrue(all(self.film_pos[f.id]<=20 for f in films))
        
        films[0].mark_as_seen(self.user)

        BasketItem.objects.create(film=films[1], wishlist=1,
                user=self.user)
        
        rating_helper.rate(self.user, 5, film_id=films[2].id)

        films = Film.get_films_to_rate(self.user, 17)
        for f in films:
            f.mark_as_seen(self.user)

        # second basket
        films = Film.get_films_to_rate(self.user, 10)
        all_films.update(f.id for f in films)
        logger.info("film ids: %r", [f.id for f in films])
        self.assertTrue(all(self.film_pos[f.id]>20 and self.film_pos[f.id]<=40 for f in films))
        for f in films:
            f.mark_as_seen(self.user)

        cache.clear()

        films = Film.get_films_to_rate(self.user, 10)
        all_films.update(f.id for f in films)
        self.assertTrue(all(self.film_pos[f.id]>20 and self.film_pos[f.id]<=40 for f in films))
        for f in films:
            f.mark_as_seen(self.user)

        films = Film.get_films_to_rate(self.user, 100)
        all_films.update(f.id for f in films)
        for f in films:
            f.mark_as_seen(self.user)
        self.assertEquals(len(films), 60)

        self.assertEquals(len(all_films), 100)

        self.assertFalse(Film.get_films_to_rate(self.user, 1))

    def test_rating_useractivity(self):
        from film20.useractivity.models import UserActivity
        from film20.core.models import UserRatingTimeRange
        from film20 import notification
        from film20.tagging.models import Tag, TaggedItem
        
        notification.models.test_queue = []

        film = Film.objects.get(permalink='pulp-fiction')
        film.save_tags('hamburger')

        film2 = Film.objects.get(permalink='the-godfather')

        Rating.objects.filter(user=self.user, film=film).delete()

        film2.rate(self.user, 8)
        film.rate(self.user, 10)
        
        activities = UserActivity.objects.filter(user=self.user) 
        self.assertEquals(len(activities), 2)

        self.assertTrue(notification.models.test_queue)

        self.assertTrue(TaggedItem.objects.get_by_model(UserActivity, 'hamburger'))

        self.assertTrue('hamburger' in [str(t) for t in Tag.objects.get_for_object(activities[0])])

    def test_anonymous_rating(self):
        from django.core.urlresolvers import reverse

        self.client = self.client_class()

        self.assertTrue(Film.objects.tagged('dramat'))

        rate_url = reverse('rate_films')
        response = self.client.get(rate_url)
        to_rate = list(response.context['films'])
        self.assertTrue(to_rate)

        request = response.context['request']
        username = request.unique_user.username
        self.assertTrue(username.startswith('tmp-'))
        self.assertNotEquals(username, 'tmp-anonymous')
        self.assertFalse(request.unique_user.id)

        self.assertFalse(User.objects.filter(username__startswith='tmp-', is_active=False))
        self.client.post('/ajax/rate-film/', {'film_id':to_rate[0].id, 'rating':10})
        user = User.objects.get(username__startswith='tmp-', is_active=False)
        username = user.username

        for i, film in enumerate(to_rate[1:]):
            self.client.post('/ajax/rate-film/', {'film_id':film.id, 'rating':i+1})

        cnt = len(to_rate)
        self.assertEquals(cnt, 6)
        
        self.assertEquals(Rating.count_for_user(user), cnt)

        left = max(0, settings.RECOMMENDATIONS_MIN_VOTES_USER - cnt)

        if left:
            for i in range(left / settings.RATING_FILMS_NUMBER + 1):
                response = self.client.get(rate_url)
                for film in list(response.context['films']):
                    self.client.post('/ajax/rate-film/', {'film_id':film.id, 'rating':5})
                    left -= 1
                    if not left:
                        break
        
        # extra fetch to make sure few films are marked as seen
        response = self.client.get(rate_url)
        to_rate = list(response.context['films'])
        data = {'prev_film_ids': ','.join(str(f.id) for f in to_rate)}
        self.client.post(rate_url, data)

        self.assertEquals(Rating.count_for_user(user), settings.RECOMMENDATIONS_MIN_VOTES_USER)

        self.assertTrue(Profile.objects.get(user=user).recommendations_status in (Profile.FAST_RECOMMENDATIONS, Profile.NORMAL_RECOMMENDATIONS))

        self.assertFalse(UserActivity.objects.all())

        response = self.client.post(reverse('acct_signup'), {
            'email': 'test@test.pl',
            'username': 'test_user',
            'password1': 'abcdef123',
            'password2': 'abcdef123',
        })
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response['Location'].endswith(reverse('main_page')))
        
        user = User.objects.get(username='test_user')
        
        self.assertEquals(len(rating_helper.get_user_ratings(user.id)), settings.RECOMMENDATIONS_MIN_VOTES_USER)
        self.assertTrue(len(rating_helper.get_seen_films(user)))

        # check if user has public rating activities
        activities = UserActivity.objects.filter(activity_type=UserActivity.TYPE_RATING, user=user)
        self.assertTrue(activities)

        # make sure temporary username was updated
        self.assertFalse(activities.filter(username__startswith='tmp-'))


