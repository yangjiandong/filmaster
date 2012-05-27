from api.tests.utils import ApiTestCase
from django.utils import simplejson as json
from film20.showtimes.models import *
import logging
logger = logging.getLogger(__name__)

class ShowtimesTest(ApiTestCase):
  
    def test_showtimes(self):
        # non-existent user or film should return 404

        pl = Country.objects.get(code='PL')
        
        town = Town(country=pl, name="Warszawa", has_cinemas=True, timezone_id="Europe/Warsaw")
        town.save()
        
        cinema = Channel(type=Channel.TYPE_CINEMA, name="Test cinema", town=town, longitude="20.994666", latitude="52.241940")
        cinema.save()
        logger.info("type: %r", cinema.type)
        
        movie = Film.objects.get(permalink='pulp-fiction')
        film = FilmOnChannel(film=movie, key='pulp-fiction', title='Pulp Fiction', match=9)
        film.save()

        movie2 = Film.objects.get(permalink='the-shawshank-redemption')
        film2 = FilmOnChannel(film=movie2, key='the-shawshank-redemption', title='The Shawshank Redemption', match=9)
        film2.save()

        time = datetime.datetime.strptime("2010-12-31 23:00", "%Y-%m-%d %H:%M")
        s = Screening(channel = cinema, film = film, utc_time = time)
        s.save()

        time = datetime.datetime.strptime("2011-01-01 2:00", "%Y-%m-%d %H:%M")
        s = Screening(channel = cinema, film = film2, utc_time = time)
        s.save()
        
        status, data = self.get("/town/%s/showtimes/2010-12-31/?with_past" % town.pk)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects'][0]['channels']), 1)
        
        status, data = self.get("/town/%s/cinema/showtimes/2010-12-31/?with_past&order=title&timezone=Europe/London" % town.pk)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)
        self.assertEquals(len(data['objects'][0]['films']), 2)
        self.assertTrue(data['objects'][0]['films'][0]['film']['title'] < data['objects'][0]['films'][1]['film']['title'])

        status, data = self.get("/town/%s/cinema/showtimes/2010-12-31/?with_past&order=-title&timezone=Europe/London" % town.pk)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)
        self.assertEquals(len(data['objects'][0]['films']), 2)
        self.assertTrue(data['objects'][0]['films'][0]['film']['title'] > data['objects'][0]['films'][1]['film']['title'])

        # go East
        status, data = self.get("/town/%s/cinema/showtimes/2010-12-31/?with_past&timezone=Europe/Moscow" % town.pk)
        logger.info(data)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)
        self.assertEquals(len(data['objects'][0]['films']), 1)
        
        status, data = self.post('/screening/%s/checkin/' % s.pk, {'user_uri':'%s/user/bob/' % self.API_BASE}, 'bob')
        self.assertEquals(status, 200)

        status, data = self.put('/screening/%s/checkin/alice/' % s.pk, {}, 'bob')
        self.assertEquals(status, 401)

        import time
        time.sleep(2)

        status, data = self.put('/screening/%s/checkin/alice/' % s.pk, {}, 'alice')
        self.assertEquals(status, 200)
        
        status, data = self.get('/screening/%s/checkin/' % s.pk)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 2)

        status, data = self.get('/screening/%s/checkin/' % s.pk, 'bob')
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 2)
        
        self.assertTrue(data['objects'][0]['created_at'] < data['objects'][1]['created_at'])
        
        status, _ = self.delete(data['objects'][0]['resource_uri'], 'alice')
        self.assertEquals(status, 401)

        status, _ = self.delete(data['objects'][0]['resource_uri'], 'bob')
        self.assertEquals(status, 200)
        
        status, data = self.get('/screening/%s/checkin/' % s.pk)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)
        
        # film checkin (no screening)
        status, data = self.post('/checkin/', {'film_uri':self.API_BASE + '/film/pulp-fiction/'}, 'alice')
        self.assertEquals(status, 200)

        status, data = self.get('/film/pulp-fiction/checkin/')
        self.assertEquals(status, 200)
        

        status, data = self.get('/user/test/channels/')
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 0)

        channel = Channel(type=Channel.TYPE_TV_CHANNEL, name="Channel", country=pl)
        channel.save()
        
        channel = Channel(type=Channel.TYPE_TV_CHANNEL, name="Test TV Channel", country=pl)
        channel.save()
        
        status, data = self.get('/country/PL/tvchannel/')
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 2)

        status, data = self.get('/country/PL/tvchannel/?q=test+tv')
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)
        
        d = dict(
            channel_uri='%s/channel/%d/' % (self.API_BASE, channel.pk),
        )
        
        status, data = self.post('/user/test/channels/', d, 'bob')
        self.assertEquals(status, 401)
        
        status, data = self.post('/user/test/channels/', d, 'test')
        self.assertEquals(status, 200)
        
        d = dict(
            channel_uri='%s/channel/%d/' % (self.API_BASE, cinema.pk),
        )
        status, data = self.post('/user/test/channels/', d, 'test')
        self.assertEquals(status, 200)

        status, data = self.get('/user/test/channels/')
        self.assertEquals(len(data['objects']), 2)

        status, data = self.get('/user/test/channels/?type=1')
        self.assertEquals(len(data['objects']), 1)

        status, data = self.get('/user/test/channels/?type=2')
        self.assertEquals(len(data['objects']), 1)

