import urlparse, cgi, json, urllib2

class InvalidURL(Exception):
    pass

class VideoMetaMeta(type):
    def __new__(cls, name, bases, *args, **kw):
        c = super(VideoMetaMeta, cls).__new__(cls, name, bases, *args, **kw)
        c.register()
        return c

class VideoMeta(object):
    __metaclass__ = VideoMetaMeta
    _fetchers = []
    
    @classmethod
    def fetch(cls, url):
        for fetcher in cls._fetchers:
            try:
                return fetcher(url)
            except InvalidURL, e:
                pass
        raise InvalidURL()
    
    @classmethod
    def register(cls):
        if cls.__name__ != 'VideoMeta':
            cls._fetchers.append(cls)

    def __unicode__(self):
        return "<%s: %s, %s>" % (self.__class__.__name__, self.thumbnail, self.duration)

    def __repr__(self):
        return unicode(self)

class YoutubeVideoMeta(VideoMeta):
    def __init__(self, url):
        vid = None
        parsed = urlparse.urlparse(url)
        if parsed.netloc in ['youtube.com', 'www.youtube.com']:
            vid = dict(cgi.parse_qsl(parsed.query)).get('v')
        elif parsed.netloc == 'youtu.be':
            vid = parsed.path[1:]
        if not vid:
            raise InvalidURL()
        gdata_url = 'http://gdata.youtube.com/feeds/api/videos/%s?alt=json' % vid
        gdata = json.loads(urllib2.urlopen(gdata_url).read())
        thumbnails = gdata['entry']['media$group']['media$thumbnail']

        self.duration = int(gdata['entry']['media$group']['yt$duration']['seconds'])
        self.thumbnail = thumbnails and thumbnails[0:3][-1].get('url') or None

class VimeoVideoMeta(VideoMeta):
    def __init__(self, url):
        vid = None
        parsed = urlparse.urlparse(url)
        if parsed.netloc in ['vimeo.com']:
            vid = parsed.path[1:]
        if not vid:
            raise InvalidURL()
        data_url = "http://vimeo.com/api/v2/video/%s.json" % vid
        data = json.loads(urllib2.urlopen(data_url).read())
        self.duration = int(data[0]['duration'])
        self.thumbnail = data[0].get('thumbnail_medium')

class DailyMotionVideoMeta(VideoMeta):
    def __init__(self, url):
        vid = None
        parsed = urlparse.urlparse(url)
        if parsed.netloc in ['www.dailymotion.pl', 'www.dailymotion.com'] and parsed.path.startswith('/video/'):
            vid = parsed.path
        if not vid:
            raise InvalidURL()
        data_url = "https://api.dailymotion.com%s?fields=duration,thumbnail_medium_url" % vid
        data = json.loads(urllib2.urlopen(data_url).read())
        self.duration = int(data['duration'])
        self.thumbnail = data.get('thumbnail_medium_url')
        
