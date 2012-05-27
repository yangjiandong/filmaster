# Python
from haystack.sites import site

# Django
from django.contrib.auth.models import User

# Project
from film20.core.models import Rating, Film
from film20.import_ratings.models import ImportRatings, ImportRatingsLog
from film20.utils.test import TestCase
    
class ImportTestCase(TestCase):
    
    def setUp(self):
        f1 = Film(type=1, permalink='the-alien', imdb_code=111,
                  status=1, version=1, release_year=1979, title='The Alien', 
                  popularity=1, popularity_month=1)
        f1.save()
        f2 = Film(type=1, permalink='the-shawshank-redemption', imdb_code=112,
                  status=1, version=1, release_year=1994, 
                  title='The Shawshank Redemption', popularity=1, 
                  popularity_month=1)
        f2.save()
        f3 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=113, 
                  status=1, version=1, release_year=1991, 
                  title='Terminator 2: Judgment Day', popularity=1, 
                  popularity_month=1)
        f3.save()
        f4 = Film(type=1, permalink='american-history-x', imdb_code=114, 
                  status=1, version=1, release_year=1998, 
                  title='American History X', popularity=1, popularity_month=1)
        f4.save()
        f5 = Film(type=1, permalink='the-big-lebowski', imdb_code=115, 
                  status=1, version=1, release_year=1998, 
                  title='The Big Lebowski', popularity=1, popularity_month=1)
        f5.save()
        f6 = Film(type=1, permalink='the-goonies', imdb_code=116, status=1, 
                  version=1, release_year=1985, title='The Goonies', 
                  popularity=1, popularity_month=1)
        f6.save()
        f7 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', 
                  imdb_code=117, status=1, version=1, release_year=2001, 
                  title='The Lord of the Rings: Fellowship of the Ring', 
                  popularity=1, popularity_month=1)
        f7.save()
        f8 = Film(type=1, permalink='nine', imdb_code=118, status=1,
                   version=1, release_year=2009, title='Nine',
                   popularity=1, popularity_month=1)
        f8.save()
        f10 = Film(type=1, permalink='xiao-cai-feng', imdb_code=119, status=1, 
                   version=1, release_year=2002, title='Xiao cai feng', 
                   popularity=1, popularity_month=1)
        f10.save()
        f11 = Film(type=1, permalink='bebes', imdb_code=120, status=1, 
                   version=1, release_year=2010, title='Bebe(s)', 
                   popularity=1, popularity_month=1)
        f11.save()
        f12 = Film(type=1, permalink='rope', imdb_code=121, status=1, 
                   version=1, release_year=1948, title='Rope', 
                   popularity=1, popularity_month=1)
        f12.save()
        f13 = Film(type=1, permalink='larry-crowne', imdb_code=122, status=1,
                   version=1, release_year=2011, title='Larry Crowne',
                   popularity=1, popularity_month=1)
        f13.save()
        f14 = Film(type=1, permalink='we-live-in-public', imdb_code=123, status=1, 
                  version=1, release_year=2009, title='We live in public', 
                  popularity=1, popularity_month=1)
        f14.save()
        f9 = Film(type=1, permalink='krotki-film-o-zabijaniu', imdb_code=124,
                  status=1, version=1, release_year=1980, 
                  title='Krotki film o zabijaniu', popularity=1, 
                  popularity_month=1)
        f9.save()

        self.u1 = User(username='michuk', email='borys.musielak@gmail.com')
        self.u1.save()

    def tearDown(self):
#        User.objects.all().delete()
        Film.objects.all().delete()
        Rating.objects.all().delete()
        ImportRatings.objects.all().delete()
        ImportRatingsLog.objects.all().delete()
