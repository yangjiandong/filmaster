#-*- coding: utf-8 -*-
from film20.core.management.base import BaseCommand
from film20.import_films.imdb_fetcher import get_movies_by_title_and_directors, save_movie_to_db
from film20.showtimes.models import FilmOnChannel, Cinema, Screening, Channel
from film20.tagging.models import Tag
from film20.festivals.models import Festival

from optparse import make_option

import re
import datetime
import pytz

timezone = pytz.timezone("Europe/London")

import logging
logger = logging.getLogger(__name__)

from beautifulsoup import BeautifulSoup as BS, class_test as ct, tag_text
from urllib import urlopen

import re

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
      make_option('--tag',
                  dest='tag',
                  default=None,
                  help='Festival tag',
      ),
    )
    
    BASE_URL = 'http://www.bfi.org.uk'

    def get_soup(self, path):
        return BS(urlopen(self.BASE_URL + path).read())

    def get_screening_datetime(self, h, m, day):
        h, m, day = int(h), int(m), int(day)
        start_date = datetime.datetime(*self.festival.start_date.timetuple()[0:3])
        month = start_date.month
        if day < start_date.day:
            month += 1
        return start_date.replace(hour=h, minute=m, day=day, month=month)

    
    def parse_t(self, t):
        date = tag_text(t.find(ct('perf_date')))
        day = re.match("\w+\s*(\d+)", date).group(1)
        h, m = re.match("(\d+):(\d+)", tag_text(t.find(ct('perf_time')))).groups()
        venue = tag_text(t.find(ct('perf_venue'))).strip()
        theater = self.get_theater(venue)
        if not theater:
            logger.warning('no theater found for %r', venue)
            return
        t = self.get_screening_datetime(h, m, day)
        return theater, pytz.timezone(theater.timezone_id).localize(t), venue

    def parse_film(self, soup):
        title = soup.find(id="header-one-films")
        title = title and tag_text(title.find('h1'))
        props = soup.findAll(ct('screening-with-credits-item')) 
        props = dict((
            tag_text(p.find(ct('screening-with-credits-left'))), 
            tag_text(p.find(ct('screening-with-credits-right')))
            ) for p in props)
        directors = [i.strip() for i in props.get('Director', '').split(',')]
        synopsis = tag_text(soup.find(ct('program-item-alternatetitle')))
        try:
            year = props.get('Year')
            year = year and int(year) or None
        except ValueError:
            year = None


        return {
                'title': title,
                'directors':filter(bool, directors),
                'year':year,
                'synopsis':synopsis,
                }

    def films(self):
        for i in range(20111012, 20111028):
            path  = '/lff/calendar/%d' % i
            soup = self.get_soup(path)
            films = soup.findAll(ct('calendar-teaser-timeblock'))
            for f in films:
                showtimes = f.findAll(ct('perf_row'))
                times = [self.parse_t(t) for t in showtimes]
                times = [t for t in times if t]
                details = self.get_soup(f.find(ct('show_title')).find('a')['href'])
                parsed = self.parse_film(details)
                parsed['times'] = times
                title = parsed.get('title')
                if title:
                    yield parsed

    def get_theater(self, name):
        name = re.sub(r'\s*\d+$', '', name.lower().strip())
        if not name in self.THEATER_MAP:
            name = re.match(r'[a-z]+', name).group(0)
        if name in self.THEATER_MAP:
            return Cinema.objects.get(id=self.THEATER_MAP[name])

    def fetch_from_imdb(self, film):
        matches = get_movies_by_title_and_directors(film['title'], film['directors'], distance=2)
        if len(matches) == 1:
            movie, status = save_movie_to_db(matches[0])
            if movie:
                logger.info("film %s imported", movie)
            else:
                logger.warning("film %r do not saved", film)
                return
            return movie
        elif not matches:
            logger.warning("no imdb movie for %r %r", film['title'], film['directors'])
        else:
            logger.warning("too many matches for %r", film['title'])

    THEATER_MAP = {
            u'cin': 542,
            u'cine': 542,
            u'curzon': 523, 
            u'empire': 508, 
            u'ica': 522,
            u'nft': 518, 
            u'odeon west end': 506,
            u'odeon leicester sq.': 507,
            u'project': 518,
            u'queen elizabeth hall': 4080,
            u'ritzy': 533,
            u'studio': 518,
            u'vue': 512,
            }

    def update_film(self, film, data):
        localized_film = film.get_localized_film('en')
        descr = localized_film and (localized_film.description or localized_film.fetched_description)
        synopsis = data.get('synopsis', '')
        print synopsis
        if not descr and synopsis:
            film.save_description(synopsis, 'en')
        for lang in ('en', 'pl'):
            localized_obj = film.get_localized_object(lang)
            tags = localized_obj and localized_obj.tag_list or ''
            tags = filter(bool, (t.strip() for t in tags.split(',')))
            if not self.festival.tag in tags:
                tags.append(self.festival.tag)
                film.save_tags(u', '.join(tags), lang)


    def handle(self, *args, **kw):
        from film20.import_films.imdb_fetcher import save_poster
        tag = kw.get('tag')

        self.festival = Festival.objects.get(tag=tag)
        theaters = Cinema.objects.filter(id__in=self.THEATER_MAP.values())
#        theaters = list(Cinema.objects.filter(id__in=self.THEATERS.values()))
#        assert len(theaters) == 2
        self.festival.theaters.add(*theaters)

#        theaters = festival.theaters.all()


#        cinemas = set()
        for film in self.films():
#            cinemas.update(cin for (cin, _, _) in film['times'])
#            print cinemas
            foc = FilmOnChannel.objects.match(film, source="festival_" + tag)
            if not foc.film:
                foc.film = self.fetch_from_imdb(film)
            if foc.film:
                self.update_film(foc.film, film)
            foc.save()
            print film['title'], foc.film and 'matched' or 'unmathed'

            for (cin, t, info) in film['times']:
                t = t.astimezone(pytz.utc).replace(tzinfo=None)
                Screening.objects.get_or_create(channel_id=cin.id, utc_time=t, film=foc, info=info)
                c = Cinema.objects.get(id=cin.id)
                c.last_screening_time = c.last_screening_time and max(c.last_screening_time, t) or t
                c.save()

