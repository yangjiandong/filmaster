from optparse import make_option
from django.conf import settings
from film20.utils.auth import oauth_opener
from film20.core.management.base import BaseCommand, make_option
import oauth

"""
A simple demo that reads in an XML document and spits out an equivalent,
but not necessarily identical, document.
"""

import sys, string, time, json

from xml.sax import saxutils, handler, make_parser
import lxml.sax
import lxml.etree
from lxml.cssselect import CSSSelector

import logging
logger = logging.getLogger(__name__)

# --- The ContentHandler

class NetflixCatalogueParser(handler.ContentHandler):

    TITLE = ('catalog_titles', 'catalog_title')

    def __init__(self):
        handler.ContentHandler.__init__(self)
        self.path = ()
        self.now = time.time()

    # ContentHandler methods
        
    def startDocument(self):
        pass

    def is_subtree(self):
        return self.path[:len(self.TITLE)] == self.TITLE

    def startElement(self, name, attrs):
        self.path = self.path + (name, )
        if self.is_subtree():
            if self.path == self.TITLE:
                self.current_title_handler = lxml.sax.ElementTreeContentHandler()
            attrs = dict(((None, name), val) for (name, val) in attrs.items())
            self.current_title_handler.startElement(name, attrs)

    def endElement(self, name):
        assert self.path[-1] == name
        if self.is_subtree():
            self.current_title_handler.endElement(name)
            if self.path == self.TITLE:
                self.process()
        self.path = self.path[:-1]

    def characters(self, content):
        if self.is_subtree():
            self.current_title_handler.characters(content)

    def ignorableWhitespace(self, content):
        if self.is_subtree():
            self.current_title_handler.ignorableWhitespace(content)

    def _items(self, selector):
        return CSSSelector(selector)(self.current_title_handler.etree)

    def _first(self, selector):
        items = self._items(selector)
        if items:
            return items[0]

    def process(self):
        title = self._first('catalog_title > title')
        id = self._first('catalog_title > id')
        dirs = self._items('catalog_title > link[title=directors] > people > link')
        
        def avail(i):
            parent = i.getparent()
            available_from = int(parent.get('available_from'))
            available_until = int(parent.get('available_until'))
            return available_from < self.now < available_until
        instant = [i for i in self._items('delivery_formats > availability > category[term=instant]') if avail(i)]

        title = title is not None and title.get('regular') or None
        id = id is not None and id.text or None

        if dirs and id and title:
            from film20.showtimes.models import FilmOnChannel
            data = instant and json.dumps(dict(instant=True)) or None
            if data:
                print data
            movie = dict(
                     directors = [d.get('title') for d in dirs],
                     title = title,
                     data = data
            )
            foc = FilmOnChannel.objects.match(movie, source='netflix', key=id)
            if foc.data != data:
                foc.data = data
                foc.save()
            print id, foc, foc.film and 'matched' or 'unmatched'

    # def processingInstruction(self, target, data):
    #     self._out.write('<?%s %s?>' % (target, data))

consumer = oauth.OAuthConsumer(settings.NETFLIX_APP_KEY, settings.NETFLIX_APP_SECRET)
opener = oauth_opener(consumer, None)

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
      make_option('--fetch-catalogue',
                  dest='fetch_catalogue',
                  default=None,
                  help='Fetches full netflix catalogue in xml format',
      ),
      make_option('--process-catalogue',
                  dest='process_catalogue',
                  default=None,
                  help='Processes netflix catalogue file',
      ),
    )
    def handle(self, *args, **kw):
        catalogue_file = kw.get('fetch_catalogue')
        if catalogue_file:
            cnt = 0
            catalogue=opener.open('http://api.netflix.com/catalog/titles/full?output=json')
            out = open(catalogue_file, 'w')
            while True:
                data = catalogue.read(1000000)
                if len(data)>0:
                    out.write(data)
                    cnt += 1
                    print cnt
                else:
                    break
            out.close()
            return

        process_catalogue = kw.get('process_catalogue')
        if process_catalogue:
            
            parser = make_parser()
            parser.setContentHandler(NetflixCatalogueParser())
            parser.parse(open(process_catalogue))

