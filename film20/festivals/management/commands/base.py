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

class BaseFestivalImporter(BaseCommand):
    option_list = BaseCommand.option_list + (
      make_option('--tag',
                  dest='tag',
                  default=None,
                  help='Festival tag',
      ),
      make_option('--test',
                  dest='test',
                  default=False,
                  action='store_true',
                  help='Test mode, no db changes',
      ),
      make_option('--auto-import',
                  dest='auto_import',
                  default=False,
                  action='store_true',
                  help='Auto import from imdb',
      ),
    )

    def open_file(self, filename):
        import os
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return open(os.path.join(base_dir, 'data', filename))

    @classmethod
    def parse(cls, data):
        import lxml.html.soupparser
        return lxml.html.soupparser.fromstring(data)
    
    @classmethod
    def tag_text(cls, el):
        return etree.tostring(el, method='text', encoding=unicode) 

    TIME_RE = re.compile("(\d+)(\s*:(\d+))?(pm|am|)", re.I)
    
    @classmethod
    def parse_ampm_time(cls, tm):
        match = cls.TIME_RE.match(tm.strip())
        if match:
            h, _, m, ampm = match.groups()
            ampm = ampm.lower() or 'pm'
            h = int(h)
            m = m is not None and int(m) or 0

            if h == 12:
                h = 0
            if ampm == 'pm':
                h += 12
            return h, m
        else:
            logger.warning("Can't parse date: %r", tm)

    def get_screening_datetime(self, h, m, day):
        h, m, day = int(h), int(m), int(day)
        start_date = datetime.datetime(*self.festival.start_date.timetuple()[0:3])
        month = start_date.month
        if day < start_date.day:
            month += 1
        return start_date.replace(hour=h, minute=m, day=day, month=month)

    def films(self):
        """
        iterator yielding dictionaries describing films, with following keys: 'title', 'directors', 'times'
        'times' is list of screenings, each screening is tuple of (theater, time with tzinfo, screening descr)
        """

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
        """
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
        """
        tag_list = film.get_tags()
        tags = filter(bool, (t.strip() for t in tag_list.split(',')))
        if not self.festival.tag in tags:
            tag_list += (tag_list and ',' or '') + self.festival.tag
            film.save_tags(tag_list)

    def handle(self, *args, **kw):
        from film20.import_films.imdb_fetcher import save_poster
        tag = kw.get('tag')
        self.auto_import = kw.get('auto_import')
        self.test = kw.get('test')

        self.festival = Festival.objects.get(tag=tag)
        self.theaters = self.festival.get_theaters()

        for film in self.films():
            logger.debug("%r", film)
            foc = FilmOnChannel.objects.match(film, source="festival_" + tag, save=not self.test)
            if foc.film:
                logger.info("%(title)s matched", film)
            else:
                logger.warning("\"%(title)s\" unmatched", film)
            if self.test:
                continue
            if not foc.film and self.auto_import:
                foc.film = self.fetch_from_imdb(film)
            if foc.film:
                self.update_film(foc.film, film)
            foc.save()

            for (cin, t, info) in film['times']:
                if not t.tzinfo:
                    t = pytz.timezone(cin.timezone_id).localize(t)
                t = t.astimezone(pytz.utc).replace(tzinfo=None)
                Screening.objects.get_or_create(channel_id=cin.id, utc_time=t, film=foc, info=info)
                c = Channel.objects.get(id=cin.id)
                c.last_screening_time = c.last_screening_time and max(c.last_screening_time, t) or t
                c.save()
        
        # flush festival cache
        if not self.test:
            self.festival.save()


