# -!- coding: utf-8 -!-
import urlparse
import urllib, urllib2
import cookielib
import lxml.html.soupparser
import lxml.etree
from lxml.cssselect import CSSSelector as Sel
import re
import json
from film20.core.models import Film

import logging
logger = logging.getLogger(__name__)

class MatcherError(Exception):
    def __init__(self):
        super(MatcherError, self).__init__(self.__class__.__name__)

class ParseError(MatcherError):
    pass

class URLMatcherMeta(type):
    def __new__(cls, name, bases, *args, **kw):
        c = super(URLMatcherMeta, cls).__new__(cls, name, bases, *args, **kw)
        c.register()
        return c

class ExtraHeadersHandler(urllib2.BaseHandler):
    def __init__(self, headers=None):
        self.handler_order = 100
        self.headers = headers or {}

    def http_request(self, request):
        for (k, v) in self.headers.items():
            request.add_header(k, v)
        return request

    https_request = http_request

class URLMatcher(object):
    __metaclass__ = URLMatcherMeta
    _matchers = {}
    
    title = ''
    directors = ()
    
    @classmethod
    def fetch(cls, url):
        parsed = urlparse.urlparse(url)
        matcher = cls._matchers.get(parsed.netloc)
        if matcher:
            try:
                return matcher(url)
            except ParseError, e:
                logger.exception(e)
                return

    @classmethod
    def register(cls):
        for domain in getattr(cls, 'domains', ()):
            cls._matchers[domain] = cls

    def match_film(self):
        matches = Film.objects.match(self.title, directors=self.directors)
        return len(matches) == 1 and matches[0] or None

    UA = "mozilla/4.0 (compatible; msie 8.0; windows nt 6.1)"
    #UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
    LANG = "en"
    _opener = None

    @property
    def url_opener(self):
        if not self._opener:
            cookie_jar = cookielib.MozillaCookieJar()
            cookie_processor = urllib2.HTTPCookieProcessor(cookie_jar)
            extra_headers = ExtraHeadersHandler({
                'user-agent': self.UA,
                'accept-language': self.LANG,
            })
            self._opener = urllib2.build_opener(cookie_processor, extra_headers)
            self._opener.version = self.UA
        return self._opener

    def parse(self, url):
        html = self.url_opener.open(url).read()
        return lxml.html.soupparser.fromstring(html)

    @classmethod
    def text_content(cls, nodes):
        return '\n'.join(j for j in (i.text_content().strip() for i in nodes) if j)

    def txt_to_list(self, txt):
        return filter(bool, (i.strip() for i in re.split(' i | et | and |,|;', txt)))

    def __unicode__(self):
        return "<%s: %s, %s>" % (self.__class__.__name__, self.title, self.directors)

    def __repr__(self):
        return unicode(self)

class WikipediaMatcher(URLMatcher):
    domains = ['en.wikipedia.org', 'pl.wikipedia.org', 'de.wikipedia.org']
    def __init__(self, url):
        data = self.parse(url)
        rows = Sel('tr')(data)
        info = {}
        for row in rows:
            td = Sel('th, td')(row)
            info[self.text_content(td[0:1]).strip()] = self.text_content(td[1:2])
        directors = info.get(u'Directed by') or info.get(u'Reżyseria') or info.get(u'Regie')
        self.directors = directors and [i.strip() for i in directors.split('\n') if i.strip()] or ()
        self.title = self.text_content(Sel('#firstHeading')(data))
        self.title = self.title.replace('(film)', '').strip()
        if not directors or not self.title:
            raise ParseError()

class FacebookMatcher(URLMatcher):
    domains = ['www.facebook.com']

    def parse(cls, url, debug=False):
        parsed = super(FacebookMatcher, cls).parse(url)
        if debug:
            print lxml.etree.tostring(parsed)
        # fix markup - uncomment commented parts
        code = Sel('code')(parsed)
        for c in Sel('code')(parsed):
            for i in c:
                if isinstance(i, lxml.html.HtmlComment):
                    p = lxml.html.soupparser.fromstring(i.text_content())
                    c.append(p)
        return parsed

    def __init__(self, url):
        while True:
            parsed = self.parse(url)
            if self.text_content(Sel('head>title')(parsed)) == 'Redirecting...':
                script = ''.join(s.text_content() for s in Sel('script')(parsed))
                m = re.search('window\.location\.replace\(("[^"]*")\)', script)
                if m:
                    redir_url = json.loads(m.group(1))
                    if redir_url not in ('http://www.facebook.com/', ):
                        url = redir_url
                        continue
                    """
                    creds = {}
                    login_page = self.parse('https://www.facebook.com/login.php?login_attempt=1')
                    for i in Sel('#login_form input')(login_page):
                        creds[i.attrib.get('name')] = i.attrib.get('value')
                    print creds
                    print 'redirect, logging in'
                    """
                    creds = {}
                    creds['email'] = 'mrk+fa@sed.pl'
                    creds['pass'] = 'qwerty'
                    data = self.url_opener.open('https://www.facebook.com/login.php?login_attempt=1', urllib.urlencode(creds)).read()
                    parsed = self.parse(url)
                    break
            else:
                break
        about = [a for a in Sel('#fbTimelineNavTopRow a')(parsed) if a.text_content() == 'About']
        if about:
            self.title = Sel('#fbProfileCover div.name h2 a')(parsed)[0].text_content()
            about_parsed = self.parse(about[0].attrib['href'])
            for t in Sel('th.label')(about_parsed):
                p = t.getparent()
                label = Sel('th.label')(p)[0].text_content()
                data = Sel('.data')(p)[0].text_content()
                if label == 'Directed By':
                    self.directors = self.txt_to_list(data)
        if self.title and self.directors:
            return

        wiki_links = Sel('.attribution a')(parsed)
        # print self.text_content(wiki_links)
        for a in wiki_links:
            href = a.attrib.get('href', '')
            if re.match('http://.*\.wikipedia\.org', href):
                w = WikipediaMatcher(href)
                self.title = w.title
                self.directors = w.directors
                break

        if not self.title or not self.directors:
            raise ParseError()

class FilmwebMatcher(URLMatcher):
    domains = ['www.filmweb.pl']

    def __init__(self, url):
        parsed = self.parse(url)
        if len(Sel('#goToLink')(parsed)):
            parsed = self.parse(url)
        self.title = self.text_content(Sel('h1.pageTitle')(parsed))
        if not self.title:
            raise ParseError()
        rows = Sel('#filmTeaserBox .info-box table tr')(parsed)
        info = {}
        for row in rows:
            tds = Sel('th, td')(row)
            if len(tds) == 2:
                label, txt = tds
                info[unicode(label.text_content())] = unicode(txt.text_content())
        self.directors = self.txt_to_list(info.get(u'reżyseria:', ''))
        if not self.directors:
            raise ParseError()

class FilmasterMatcher(URLMatcher):
    domains = ['filmaster.pl', 'filmaster.com']

    def __init__(self, url):
        parsed = urlparse.urlparse(url)
        m = re.match('/film/(.*)/', parsed.path)
        if not m:
            raise ParseError()
        self.permalink = m.group(1)

    def match_film(self):
        try:
            return Film.objects.get(permalink=self.permalink)
        except Film.DoesNotExist, e:
            pass

class IMDBMatcher(URLMatcher):
    domains = ['www.imdb.com']

    def __init__(self, url):
        parsed = urlparse.urlparse(url)
        m = re.match('/title/tt(\d+)/', parsed.path)
        if not m:
            raise ParseError()
        self.imdb_code = m.group(1)

    def match_film(self):
        try:
            return Film.objects.get(imdb_code=self.imdb_code)
        except Film.DoesNotExist, e:
            pass
