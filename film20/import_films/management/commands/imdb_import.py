from film20.core.management.base import BaseCommand, make_option
import urllib2
import lxml.html.soupparser
from lxml.cssselect import CSSSelector
import re
from film20.import_films.imdb_fetcher import get_movie_by_id, save_movie_to_db

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--top-tv-series',
                  action='store_true',
                  dest='top_tv_series',
                  default=False,
        ),
    )

    BASE = 'http://www.imdb.com'
    URL = '/search/title?num_votes=5000,&sort=user_rating,desc&title_type=tv_series'
    link_selector = CSSSelector('.results td.title > a')
    next_selector = CSSSelector('.pagination a')

    def top_tv_series(self):
        url = self.URL
        while url:
            parsed = lxml.html.soupparser.parse(urllib2.urlopen(self.BASE + url))
            next = [a for a in self.next_selector(parsed) if a.text.startswith('Next')]
            url = next and next[0].get('href')
            items = self.link_selector(parsed)
            for item in items:
                imdb_id = re.match('/title/tt(\d+)', item.get('href'))
                imdb_id = imdb_id and imdb_id.group(1)
                if imdb_id:
                    yield imdb_id

    def import_movie(self, imdb_id):
        movie = get_movie_by_id(int(imdb_id), 'http')
        save_movie_to_db(movie)


    def handle(self, *args, **opts):
        if opts.get('top_tv_series'):
            for imdb_id in self.top_tv_series():
                self.import_movie(imdb_id)
        else:
            for imdb_id in args:
                self.import_movie(imdb_id)
