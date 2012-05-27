#-*- coding: utf-8 -*-
from film20.core.management.base import BaseCommand
from film20.import_films.imdb_fetcher import get_movies_by_title_and_directors, save_movie_to_db
from film20.showtimes.models import FilmOnChannel, Screening, Channel
from film20.tagging.models import Tag
from film20.festivals.models import Festival

from optparse import make_option

import urllib2
import re
import datetime
import pytz

from lxml.cssselect import CSSSelector
from lxml import etree

import logging
logger = logging.getLogger(__name__)

from urllib import urlopen

import re

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
      make_option('--tag',
                  dest='tag',
                  default=None,
                  help='Festival tag',
      ),
      make_option('--auto-import',
                  dest='auto_import',
                  default=False,
                  action='store_true',
                  help='Auto import from imdb',
      ),
    )
    
    BASE_URL = 'http://www.americanfilmfestival.pl'

    @classmethod
    def parse(cls, data):
        import lxml.html.soupparser
        return lxml.html.soupparser.fromstring(data)

    def get_screening_datetime(self, h, m, day):
        h, m, day = int(h), int(m), int(day)
        start_date = datetime.datetime(*self.festival.start_date.timetuple()[0:3])
        month = start_date.month
        if day < start_date.day:
            month += 1
        return start_date.replace(hour=h, minute=m, day=day, month=month)
    
    def parse_t(self, el):
        tm = CSSSelector('.czas b')(el)[0].text
        try:
            venue = CSSSelector('.czas span')(el)[0].text.strip()
        except IndexError:
            venue = ''
        day, h, m = re.match("(\d+) [^\d]*(\d+):(\d+)", tm).groups()
        theater = self.get_theater(venue)
        t = self.get_screening_datetime(h, m, day)
        return theater, pytz.timezone(theater.timezone_id).localize(t), venue


    def _urls(self):
        for day in range(15, 21):
            for tm in ("9:30", "12:30", "15:15", "18:00", "20:45"):
                yield self.BASE_URL + "/lista.do?typ=dz&czas=%s&dzien=%s" % (tm, day)
            
    def films(self):
        for url in self._urls():
            data = urllib2.urlopen(url)
            root = self.parse(data)

            for f in CSSSelector('.wynikiwysz > tr')(root):
                try:
                    title_localized = CSSSelector('.tytulgl a')(f)[0].text
                except IndexError, e:
                    continue
                try:
                    title = CSSSelector('.tytul a')(f)[0].text
                except IndexError, e:
                    title = title_localized

                footer = CSSSelector('.stopka')(f)[0].text
                footer = [i.strip() for i in footer.split('/')]
                directors = footer and filter(bool, (d.strip() for d in footer[0].split(','))) or ()
                
                times = [self.parse_t(f)]
                
                yield {
                        'title':title,
                        'directors':directors,
                        'times':times,
                }

    def get_theater(self, name):
        return self.theaters[0]

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

    def update_film(self, film, data):
        localized_film = film.get_localized_film('en')
        descr = localized_film and (localized_film.description or localized_film.fetched_description)
        synopsis = data.get('synopsis', '')
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
        self.auto_import = kw.get('auto_import')

        self.festival = Festival.objects.get(tag=tag)
        self.theaters = self.festival.get_theaters()
        
        for film in self.films():
            foc = FilmOnChannel.objects.match(film, source="festival_" + tag)
            if not foc.film and self.auto_import:
                foc.film = self.fetch_from_imdb(film)
            if foc.film:
                self.update_film(foc.film, film)
            foc.save()
            print film['title'], foc.film and 'matched' or 'unmathed'

            for (cin, t, info) in film['times']:
                t = t.astimezone(pytz.utc).replace(tzinfo=None)
                Screening.objects.get_or_create(channel_id=cin.id, utc_time=t, film=foc, info=info)
                c = Channel.objects.get(id=cin.id)
                c.last_screening_time = c.last_screening_time and max(c.last_screening_time, t) or t
                c.save()

