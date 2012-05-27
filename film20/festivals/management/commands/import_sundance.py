# -!- coding: utf-8 -!-
from .base import BaseFestivalImporter
import re
import pytz

from urllib2 import urlopen
import datetime

from lxml.cssselect import CSSSelector
from lxml import etree

import logging
logger = logging.getLogger(__name__)

class Command(BaseFestivalImporter):

    THEATERS = [
            ("Peery's Egyptian Theater", 'Ogden'), 
            ('Eccles Theatre', 'Park City'), 
            ('Egyptian Theatre', 'Park City'), 
            ('Holiday Village Cinema', 'Park City'), 
            ('Library Center Theatre', 'Park City'), 
            ('MARC', 'Park City'), 
            ('New Frontier Microcinema', 'Park City'), 
            ('Prospector Square Theatre', 'Park City'), 
            ('Redstone Cinema', 'Park City'), 
            ('Temple Theatre', 'Park City'), 
            ('Yarrow Hotel Theatre', 'Park City'), 
            ('Broadway Centre Cinema', 'Salt Lake City'), 
            ('Rose Wagner Performing Arts Center', 'Salt Lake City'), 
            ('Salt Lake City Library', 'Salt Lake City'), 
            ('Tower Theatre', 'Salt Lake City'), 
            ('Screening Room', 'Sundance Resort'),
    ]

    THEATER_MAP = {
        ('Redstone Cinema', 'Park City'): ('Redstone 8 Cinemas', 'Park City'),
        ('Holiday Village Cinema', 'Park City'): ('Cinemark Holiday Village 4', 'Park City'),
        ('Broadway Centre Cinema', 'Salt Lake City'): ('Broadway Centre Theatre', 'Salt Lake City'),
        ('Tower Theatre', 'Salt Lake City'): ('Tower Theatre', 'Salt Lake City'),
        ('Screening Room', 'Sundance Resort'): ('Sundance Resort Screening Room', 'Park City'),
    }

    @classmethod
    def parse_list(cls, text):
        return filter(bool, (d.strip() for d in (text or '').split(',')))

    @classmethod
    def parse_date(cls, tm, dt):
        month, day, year = map(int, re.match("(\d+)/(\d+)/(\d+)", dt).groups())
        h, m = cls.parse_ampm_time(tm)
        return datetime.datetime(year, month, day, h, m)

    def get_theater(self, venue, city):
        from film20.showtimes.models import Channel, Town

        m = re.match("(.*)(\s+\d+)", venue)
        if m:
            venue = m.group(1)
        if (venue, city) in self.THEATER_MAP:
            venue, city = self.THEATER_MAP[(venue, city)]

        try:
            theater = Channel.objects.get(name=venue, town__name=city, town__country__code='US')
        except Channel.DoesNotExist:
            town = Town.objects.select_related('country').get(name=city, country__code='US')
            theater = Channel(
                    name=venue,
                    town=town,
                    latitude=town.latitude,
                    longitude=town.longitude,
                    type=1)
            theater.save()
        self.festival.theaters.add(theater)
        return theater

    def parse_film(self, url):
        root = self.parse(urlopen(url).read())
        title = CSSSelector('#event_title')(root)
        title = title and self.tag_text(title[0]).strip()
        j = CSSSelector('#jumbo')(root)
        meta = j and CSSSelector('p')(j[0].getparent())
        meta = meta and meta[0]
        directors = []
        for tag in meta:
            if tag.text == 'DIRECTOR':
                txt = (tag.tail or '').split("\t")[0]
                directors = self.parse_list(txt)
        screenings = CSSSelector('#timetable_list')(root)
        def parse_screening(s):
            items = [i.text for i in s]
            try:
                tm = items[0].strip()
                dt = items[1].strip()
                venue = items[3].strip()
                city = items[4].strip()
                
                if tm == 'Noon':
                    tm = "12:00pm"
                elif tm == 'Midnight':
                    tm = "12:00am"
                theater = self.get_theater(venue, city)
                return theater, self.parse_date(tm, dt), venue
            except Exception, e:
                logger.debug("items: %r", items)
                logger.warning(unicode(e))

        times = filter(bool, (parse_screening(s) for s in screenings))
        if title and directors:
            return {
                    'title': title,
                    'directors': directors,
                    'times': times,
                    }

    def fetch_films(self, url):
        root = self.parse(urlopen(url).read())
        for td in CSSSelector('td.ofg_table')(root):
            a = CSSSelector('a')(td)
            details_url = a and a[0].get('href')
            if details_url and not details_url in self.seen:
                film = self.parse_film(details_url)
                if film:
                    yield film

            self.seen.add(details_url)

    def films(self):
        self.seen = set()
        for offs in range(0, 235, 9):
            for film in self.fetch_films('http://filmguide.sundance.org/filmguide/index/%d' % offs):
                yield film

    def handle(self, *args, **kw):
        ret = super(Command, self).handle(*args, **kw)
        self.festival.invalidate_cache()
        return ret
