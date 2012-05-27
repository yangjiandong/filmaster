from django.core.files.base import ContentFile
from film20.showtimes.base_fetcher import BaseTVFetcher
from film20.showtimes.models import Channel, Country, Fetcher

from optparse import make_option
import xmltv
import urllib2
import datetime
import pytz
from itertools import groupby

class Command(BaseTVFetcher):
    option_list = BaseTVFetcher.option_list + (
        make_option('--in', dest='in', help='input xml file'),
        make_option('--force', dest='force', action="store_true"),
    )
    
    name = 'xmltv'
    
    def run(self, *args, **kw):
        input_file = self.opt.get('in')
        
        if not input_file:
            self.logger.error('--in parameter is required')
            return

        if self.opt.get('update_channels'):
            country = self.opt.get('country')
            if not country:
                self.logger.error("--country parameter is required")
                return
            try:
                country = Country.objects.get(code=country.upper())
            except Country.DoesNotExist, e:
                self.logger.error("invalid country code")
            
            for c in xmltv.read_channels(input_file):
                name = c['display-name'][0][0]
                id = c['id']
                icon = c.get('icon')
                icon_url = icon and icon[0].get('src')
                self.logger.info(icon_url)
                
                def defaults():
                    if icon_url:
                        try:
                            icon = ContentFile(urllib2.urlopen(icon_url).read())
                            icon.name = icon_url.split('/')[-1]
                            yield 'icon', icon
                        except urllib2.HTTPError, e:
                            pass
                    yield 'name', name
                    yield 'country', country
                    
                channel, created = Channel.objects.get_or_create(
                    type=Channel.TYPE_TV_CHANNEL,
                    fetcher__cid=id, 
                    fetcher__name='xmltv',
                    defaults=defaults(),
                )
                if created:
                    Fetcher(name='xmltv',
                            channel=channel,
                            cid=id).save()
                if not created and self.opt.get('force'):
                    if channel.icon:
                        channel.icon.delete()
                    for (n, v) in defaults(): 
                        setattr(channel, n, v)
                    channel.save()
            return        
        for id, programs in groupby(xmltv.read_programmes(input_file), lambda p:p['channel']):
            try:
                channel = Channel.objects.get(fetcher__name='xmltv', fetcher__cid=id)
            except Channel.DoesNotExist, e:
                self.logger.warning("channel %s does not exist, try --update-channels", id)
                continue
                
            last_time = channel.last_screening_time
            last_time = last_time and pytz.utc.localize(last_time)
            max_time = None
                
            for p in programs:
                directors = p.get('credits',{}).get('director')
                title = p.get('title')
                title = title and title[0][0]
                subtitle = p.get('sub-title')
                episode = p.get('episode-num')
                year = p.get('date')
                try:
                    year = year and int(year)
                except ValueError, e:
                    year = None
                if not directors or not title or episode or subtitle:
                    continue
                start = self.parse_time(p.get('start'))
                stop = self.parse_time(p.get('stop'))
                if last_time and start <= last_time:
                    continue
                max_time = start
                movie = dict(
                    title = title,
                    directors = directors,
                    times = [start],
                    year = year,
                )
                self.update_movie(channel, movie)

            if False and max_time:
                channel.last_screening_time = max_time.replace(tzinfo=None)
                channel.save()
                

    @classmethod
    def parse_time(cls, t):
        tm, tz = t.split()
        assert tz[0] in ('+', '-')
        sign, tz_h, tz_m = (tz[0] == '-' and -1 or 1), int(tz[1:3]), int(tz[3:5])
        tz = datetime.timedelta(seconds=sign*(tz_h*3600+tz_m*60))
        return pytz.utc.localize(datetime.datetime.strptime(tm, "%Y%m%d%H%M%S") - tz)
        
