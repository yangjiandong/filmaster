#-*- coding: utf-8 -*-
from film20.core.management.base import BaseCommand
from film20.import_films.imdb_fetcher import get_movies_by_title_and_directors, save_movie_to_db
from film20.showtimes.models import FilmOnChannel, Cinema, Screening, Channel
from film20.tagging.models import Tag
from film20.festivals.models import Festival

import re
import datetime
import pytz

timezone = pytz.timezone("Europe/Warsaw")

import logging
logger = logging.getLogger(__name__)

FESTIVAL_TAG = 'wff27'

BASE_URL = 'http://www.wff.pl'

from beautifulsoup import BeautifulSoup as BS, class_test as ct, tag_text
from urllib import urlopen

import re
SCR_RE = re.compile('\s*([^>]+)>\s*([^>]+)>\s*(\d+)([^>]+)>\s*(\d+)\.(\d+)')

START_DATE = timezone.localize(datetime.datetime(2011, 10, 7, 0, 0, 0))

class Command(BaseCommand):

    def get_soup(self, path):
        return BS(urlopen(BASE_URL + path).read())

    def parse_t(self, t):
        m = SCR_RE.match(t)
        if m:
            cin, weekday, day, month, h, min = m.groups()
            cin = re.sub("\s*\d+\s*$", "",cin).strip().lower()
            return cin, START_DATE.replace(hour=int(h), minute=int(min), day=int(day))
        logger.warning("invalid screening format: %r", t)

    def parse_film(self, soup):
        belka = soup.find(ct('ps_belka'))
        title_pl = tag_text(belka.find('h2'))
        title = tag_text(belka.find('h4'))
        rows = soup.findAll(ct('row'))
        def _row(r):
            p = tag_text(r).split(':', 1)
            if len(p) == 2:
                return p[0].strip(), p[1].strip()
            else:
                return None, None

        props = dict(_row(row)  for row in rows)

        screenings = soup.find(ct('pokazy'))
        screenings = screenings and screenings.findAll('li')[1:]
        screenings = screenings and [tag_text(s) for s in screenings] or []
        
        img_url = soup.find(ct('ps_body')).find('img')
        img_url = img_url and img_url.parent['href']

        return {
            'title':title,
            'title_localized':title_pl,
#            'props':props,
            'directors':filter(bool, [i.strip() for i in props.get(u'Reżyser', '').split(',')]),
            'times':[self.parse_t(t) for t in screenings],
            'year':props.get('Rok produkcji', None),
            'img_url':img_url,
        }

    def films(self):
        for part in ['special'] + [chr(ord('a') + i) for i in range(26)]:
            for subpage in range(10):
                path = '/filmy/wszystkie/%s/%s/' % (part, subpage)
                soup = self.get_soup(path)
                films = soup.findAll(ct('nowina'))
                if films:
                    for f in films:
                        url = '/' + f.find('a')['href']
                        details = self.get_soup(url)
                        yield self.parse_film(details)
                else:
                    break
            
    THEATERS = {
        'kinoteka': 4,
        'multikino': 5,
    }
    def handle(self, *args, **kw):
        from film20.import_films.imdb_fetcher import save_poster

        festival = Festival.objects.get(tag=FESTIVAL_TAG)
        theaters = list(Cinema.objects.filter(id__in=self.THEATERS.values()))
        assert len(theaters) == 2
        festival.theaters.add(*theaters)

        theaters = festival.theaters.all()
        cinemas = set()
        for film in self.films():
            foc = FilmOnChannel.objects.match(film, source="wff")
            matched = foc.film
            print film['title'], matched and 'matched' or 'unmathed', film['img_url']
#            if matched and film['img_url'] and not foc.film.hires_image:
#                save_poster(foc.film, film['img_url'])
#                foc.film.save()
            
            for (cin, t) in film['times']:
                Screening.objects.get_or_create(channel_id=self.THEATERS[cin], utc_time=t.astimezone(pytz.utc).replace(tzinfo=None), film=foc)
