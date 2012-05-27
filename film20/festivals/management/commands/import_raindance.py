from film20.core.management.base import BaseCommand
from film20.import_films.imdb_fetcher import get_movies_by_title_and_directors, save_movie_to_db
from film20.showtimes.models import FilmOnChannel, Cinema, Screening, Channel
from film20.tagging.models import Tag

import re
import datetime
import pytz

timezone = pytz.timezone("Europe/London")

kv_re = re.compile("([^:]+)\s*:\s*(.*)")
data_re = re.compile("(\d+)\s+(September|October)[, ]+(\d+)(\s*:(\d+))?(pm|am|)", re.I)
import logging
logger = logging.getLogger(__name__)

def parse_date(d):
    match = data_re.search(d)
    if match:
        day, month, h, _, m, ampm = match.groups()
        ampm = ampm.lower() or 'pm'
        day = int(day)
        h = int(h)
        m = m is not None and int(m) or 0
        if month == "September":
            month = 9
        else:
            month = 10

        if h == 12:
            h = 0
        if ampm == 'pm':
            h += 12
        return timezone.localize(datetime.datetime.now().replace(day=day, month=month, second=0, microsecond=0, minute=m, hour=h))
    else:
        logger.warning("Can't parse date: %r", d)

RAINDANCE_TAG = 'Raindance2011'

class Command(BaseCommand):
    def handle(self, *args, **kw):
        data = open(args[0]).read().decode('utf-8')
        films = [i.strip() for i in data.split("\r\n\r\n") if i.strip()]
       
        defaults = {
            'name':'Apollo - West End',
            'type':Cinema.TYPE_CINEMA,
            'timezone_id':'Europe/London',
            'address':'19 Regent Street, London, SW1Y 4LR, United Kingdom - 0871 220 6000',
            'latitude':'51.508971',
            'longitude':'-0.134103',
        }
        cinema, _ = Cinema.objects.get_or_create(fetcher1_id=str(0x47346eaa2f391751), defaults=defaults)
        Tag.objects.update_tags(Channel.objects.get(id=cinema.id), 'raindance2011')
        for f in films:
            lines = f.split("\r\n")
            film = {}
            film['title'] = lines[0]
            for line in lines[1:]:
                match = kv_re.match(line)
                if match:
                    k, v = match.groups()
                    k, v = k.strip().lower(), v.strip()
                    film[k] = v
            if 'director' in film and 'title' in film:
                screenings = film.get('screening') or film.get('screenings') or ''
                film['times'] = filter(bool, [parse_date(d) for d in screenings.split('|')])
                directors = film.get('director')
                if directors:
                    directors = directors.replace('&', ',').replace(' and ', ',')
                film['directors'] = directors and [d.strip() for d in directors.split(',')] or ()
                film['info'] = film.get('synopsis', '')

                logger.debug('trying to match: %r', film)
                foc = FilmOnChannel.objects.match(film, source="raindance")
                if cinema:
                    for t in film['times']:
                        Screening.objects.get_or_create(channel=cinema, utc_time=t.astimezone(pytz.utc).replace(tzinfo=None), film=foc)
                if not foc.film:
                    matches = get_movies_by_title_and_directors(film['title'], film['directors'], distance=2)
                    if len(matches) == 1:
                        movie, status = save_movie_to_db(matches[0])
                        foc.film = movie
                        foc.save()
                        if movie:
                            logger.info("film %s imported", movie)
                        else:
                            logger.warning("film %r do not saved", film)
                            assert 0
                    elif not matches:
                        logger.warning("no imdb movie for %r %r", film['title'], film['directors'])
                    else:
                        logger.warning("too many matches for %r", film['title'])
                else:
                    logger.info('film %r is already matched', film['title'])
                if foc.film:
                    localized_film = foc.film.get_localized_film('en')
                    descr = localized_film and (localized_film.description or localized_film.fetched_description)
                    synopsis = film.get('synopsis', '')
                    if not descr and synopsis:
                        foc.film.save_description(synopsis, 'en')
                    for lang in ('en', 'pl'):
                        localized_obj = foc.film.get_localized_object(lang)
                        tags = localized_obj and localized_obj.tag_list or ''
                        tags = filter(bool, (t.strip() for t in tags.split(',')))
                        logger.info(tags)
                        if not RAINDANCE_TAG in tags:
                            tags.append(RAINDANCE_TAG)
                            foc.film.save_tags(u', '.join(tags), lang)




