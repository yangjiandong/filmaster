# Python
import time
import unittest

# Django
from film20.utils.test import TestCase
from django.db import connection
from django.contrib.auth.models import User
from django.test.client import RequestFactory

# Project
from film20.core.models import Film, Object, Rating, ShortReview
from film20.config.urls import *
from film20.import_ratings.import_ratings_helper import save_rating
from film20.dashboard.views import *
from film20.utils.test import TestCase

class ExportRatingsTestCase(TestCase):
    
    def setUp(self):
        User.objects.all().delete()
        Film.objects.all().delete()
        Rating.objects.all().delete()
        ShortReview.objects.all().delete()

        #create sample user
        user1 = User.objects.create_user('michuk',
                                       'borys.musielak@gmail.com',
                                       'secret')
        user1.save()
        user2 = User.objects.create_user('john',
                                       'john.doe@gmail.com',
                                       'secret')
        user2.save()

        tags = "science-fiction comedy"

        #create sample user rating
        film1 = Film()
        film1.title = "Battlefield Earth II"
        film1.type = Object.TYPE_FILM
        film1.permalink = "battlefirld-earth-ii"
        film1.release_year = 2010
        film1.production_country_list = "USA"
        film1.save()
        film1.save_tags(tags, LANG="pl", saved_by=2)

        film2 = Film()
        film2.title = "Battlefield Earth III"
        film2.type = Object.TYPE_FILM
        film2.permalink = "battlefirld-earth-iii"
        film2.release_year = 2011
        film2.production_country_list = "USA"
        film2.save()
        film2.save_tags(tags, LANG="pl", saved_by=2)

        film3 = Film()
        film3.title = "Battlefield Earth IV"
        film3.type = Object.TYPE_FILM
        film3.permalink = "battlefirld-earth-iv"
        film3.release_year = 2012
        film3.production_country_list = "Italy"
        film3.save()
        film3.save_tags(tags, LANG="pl", saved_by=2)

        film4 = Film()
        film4.title = "Battlefield Earth V"
        film4.type = Object.TYPE_FILM
        film4.permalink = "battlefirld-earth-v"
        film4.release_year = 2013
        film4.production_country_list = "UK"
        film4.save()
        film4.save_tags(tags, LANG="pl", saved_by=2)

        
        # set up test user ratings
        save_rating(film1, user1, 1)
        save_rating(film2, user1, 3)
        save_rating(film3, user1, 4)
        save_rating(film4, user1, 6)

        save_rating(film2, user2, 2)
        save_rating(film3, user2, 3)
        save_rating(film4, user2, 5)

        users = User.objects.all()
        self.assertEquals(len(users), 2)

        films = Film.objects.all()
        self.assertEquals(len(films), 4)

        user1 = users[0].id
        ratings1 = Rating.objects.filter(Q(user=user1))
        self.assertEquals(len(ratings1), 4)

        user2 = users[1].id
        ratings2 = Rating.objects.filter(Q(user=user2))
        self.assertEquals(len(ratings2), 3)

        reviews1 = ShortReview.objects.filter(Q(user=user1))
        self.assertEquals(len(reviews1), 0)

        reviews2 = ShortReview.objects.filter(Q(user=user2))
        self.assertEquals(len(reviews2), 0)

    def test_build_ratings(self):
        users = User.objects.all()
        user1 = users[0]
        user2 = users[1]

        set1 = time.time()
        data_set1 = create_data_set(user1)
        print "Creating set for first user: " + str(time.time() - set1) + "s"
        self.assertEquals(len(data_set1), 4)

        set2 = time.time()
        data_set2 = create_data_set(user2)
        print "Creating set for second user: " + str(time.time() - set2) + "s"
        self.assertEquals(len(data_set2), 3)

    def test_request(self):
        factory = RequestFactory()
        path_url = '/' + str(urls.urls['RATED_FILMS']) + '/' + str(urls.urls['EXPORT_RATINGS'])
        format_as_str = 'xml'
        request = factory.get(path_url)

        users = User.objects.all()

        request.user = users[0]
        response = export_ratings(request, format_as_str)
        self.assertEqual(response.status_code, 200)

        request.user = users[1]
        response = export_ratings(request, format_as_str)
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        User.objects.all().delete()
        Film.objects.all().delete()
        Rating.objects.all().delete()
        ShortReview.objects.all().delete()
