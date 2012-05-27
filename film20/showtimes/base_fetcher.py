from django.core.management.base import CommandError
from django.db.models import Max

from beautifulsoup import BeautifulSoup
from optparse import make_option
import logging
import datetime
import re
import sys
import pytz

from film20.core.management.base import BaseCommand
from film20.showtimes.models import FilmOnChannel, Screening, Country
from film20.utils.texts import normalized_text

logger = logging.getLogger(__name__)

quote_re = re.compile(r'("[^"]*")([^\s])')

BeautifulSoup.MARKUP_MASSAGE += [
    (re.compile(r"<[^>]+>"), lambda tag:quote_re.sub(r"\1 \2", tag.group(0))),
    (re.compile(r"<!\[CDATA\[.*?\]\]>",re.I|re.M|re.DOTALL),lambda x:''),
    (re.compile("<script[^>]*?>.*?</script>",re.I|re.M|re.DOTALL),lambda x:''),
]

def class_test(class_name):
    def test(tag):
        return any((class_name in value.split(' ')) for (name, value) in tag.attrs if name=='class')
    return test

def tag_text(tag, **kw):
    return (' '.join(unicode(t) for t in tag.findAll(text=True, **kw))).strip()

title_re = re.compile(r'(.*)\([^\)]+\)\s*')
def normalized_title(t):
    m = title_re.match(t)
    return normalized_text(m and m.group(1) or t)

class BaseFetcher(BaseCommand):
    option_list = BaseCommand.option_list + (
      make_option('--all',
                  action='store_true',
                  dest='all',
                  default=False,
                  help='All locations'
      ),
      make_option('--day',
                  action='store',
                  dest='day',
                  default=0,
                  type='int',
                  help='Day (0-today, 1-tomorrow, etc)'
      ),
      make_option('--disable-if-no-movie',
                  action='store_true',
                  dest='disable_no_movie',
                  default=False,
                  help='Disable channels without movies',
      ),
    )

    class ScreeningsNotFound(Exception):
        pass

    def soup(self, data):
        return BeautifulSoup(data)

    def handle_base_options(self, *args, **opt):
        """
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))
        LEVEL = (logging.WARNING, logging.INFO, logging.DEBUG)
        self.logger.setLevel(LEVEL[int(opt.get('verbosity',0))])
        """
        self.logger = logger
        self.day = opt.get('day')
        self.date = datetime.date.today() + datetime.timedelta(days=self.day)
        self.all = opt.get('all')
        self.opt = opt
    
    def run(self, *args, **opt):
        raise NotImplementedError
    
    def handle(self, *args, **opt):
        self.handle_base_options(*args, **opt)
        self.run(*args, **opt)

    @classmethod
    def time_to_utc(cls, t, timezone_id=None):
        if not t.tzinfo and timezone_id:
            t = pytz.timezone(timezone_id).localize(t)
        if t.tzinfo:
            t=t.astimezone(pytz.utc).replace(tzinfo=None)
        return t

    def update_movie(self, channel, movie, timezone_id=None):
        times = [self.time_to_utc(t, timezone_id) for t in movie.get('times', ())]
        if channel.last_screening_time:
            times = filter(lambda t: t > channel.last_screening_time, times)
        if times:
            fetcher_name = getattr(self, 'name', '')
            film = FilmOnChannel.objects.match(movie, source=fetcher_name)
            logger.info("%s %s", film, "matched" if film.film else "unmatched")
            for t in times:
                Screening.objects.get_or_create(channel=channel, film=film, utc_time=t)
            return True
        else:
            logger.debug('no newer screening times for %r on %r', movie, channel)
        
    @classmethod
    def parse_tm(cls, date, t):
        try:
            hm = tuple(map(int, t.split(':')))
            return datetime.datetime(*(date.timetuple()[:3]+hm))
        except Exception, e:
            logger.warning("%s: cannot parse: %s", e, t)

    def last_screening_date(self, channel):
        from film20.showtimes.utils import DAY_START_DELTA
        if channel.last_screening_time:
            return (pytz.utc.localize(channel.last_screening_time).astimezone(self.channel_timezone(channel)) - DAY_START_DELTA).date()
    
    def channel_timezone(self, channel):
        raise NotImplementedError()

    def update_channel_screenings(self, channel):
        logger.info("update screenings for %s", channel)
        # auto detect start date using existing channel screenings
        date = self.last_screening_date(channel)
        today = datetime.datetime.now(self.channel_timezone(channel)).date()
        if date:
            logger.debug("last date form %s: %s", channel, date)
            date = date + datetime.timedelta(days=1)
            date = max(date, today)
        else:
            date = today
            
        cnt = 0
        start_date = date
        err = False

        try:
            while True:
                for movie in self.fetch_movies(channel, date):
                    logger.info("movie %s in %s", movie, channel)
                    if self.update_movie(channel, movie):
                        cnt += 1
                date += datetime.timedelta(days=1)
        except self.ScreeningsNotFound, e:
            logger.info("no more screenings for %s at %s", channel, date)
        except Exception, e:
            logger.exception(e)
            err = True

        if cnt:
            max_time = channel.screening_set.aggregate(Max('utc_time')).get('utc_time__max')
            if max_time:
                channel.last_screening_time = max_time
                channel.save()
                logger.debug("last screening time for %s: %s", channel, max_time)
        elif self.opt['disable_no_movie'] and (date - start_date).days >= 3 and not err:
          channel.is_active=False
          channel.save()
          logger.info("channel %s disabled", channel)

class BaseCinemaFetcher(BaseFetcher):
    option_list = BaseFetcher.option_list + (
      make_option('--update-cinemas',
                  action='store_true',
                  dest='update_cinemas',
                  default=False,
                  help='Update cinemas at a given location'
      ),
    )

class BaseTVFetcher(BaseFetcher):
    option_list = BaseFetcher.option_list + (
      make_option('--update-channels',
                  action='store_true',
                  dest='update_channels',
                  default=False,
                  help='Update channels'
      ),
      make_option('--country',
                  dest='country',
      ),
    )
    
    def handle_base_options(self, *args, **opt):
        super(BaseTVFetcher, self).handle_base_options(*args, **opt)
        code = opt.get('country')
        self.country = code and Country.objects.get(code=code.upper())
    
