# -*- coding: utf-8 -*-
import re
import json
import urllib
import urllib2
import unicodedata
import htmlentitydefs
from BeautifulSoup import BeautifulSoup

RE_HTML_TAGS = re.compile( r'<.*?>' )
RE_IMDB_FILM_URL = re.compile( r'imdb.com/title/tt.*/$' )
RE_WIKI_ANNOTATIONS = re.compile( r'\[(\d+)\]' )

def strip_tags( obj ):
    text = RE_HTML_TAGS.sub( '', str( obj ) )
    text = RE_WIKI_ANNOTATIONS.sub( '', text )
    return unescape( text.strip() ).decode( 'utf-8' )

def unescape( text ):
    def fixup( m ):
        text = m.group( 0 )
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr( int( text[3:-1], 16 ) )
                else:
                    return unichr( int( text[2:-1] ) )
            except ValueError:
                pass
        else:
            try:
                text = unichr( htmlentitydefs.name2codepoint[text[1:-1]] )
            except KeyError:
                pass
        return text
    return re.sub( "&#?\w+;", fixup, text )


class InfoBoxParser( object ):
    def __init__( self, soup=None, html=None ):
        if soup is None:
            soup = BeautifulSoup( html )
        self.soup = soup

    def parse( self ):
        result = {}
        infobox = self.soup.find( 'table', { 'class': re.compile( 'infobox(.*?)' ) } )
        if infobox is not None:
            for tr in infobox.findAll( 'tr' ):
                th = tr.find( 'th' )
                td = tr.find( 'td' )
                if th is None:
                    image = td.find( 'a', { 'class': 'image' } )
                    if image is not None:
                        src = image.img.get( 'src', None )
                        th = '__IMAGE__'
                        td = 'http:' + '/'.join( src.replace( '/thumb', '' ).split('/')[:-1] )
                result[strip_tags( th ) ] = td
        return result

class FilmInfoBoxParser( InfoBoxParser ):
    def parse( self ):
        raw = super( FilmInfoBoxParser, self ).parse()
        if raw:
            return self.generate( raw )
    
    def generate( self, data ):
        result = {
            'release_date': None,
            'release_year': None,
            'poster_url'  : None,
            'director'    : None,
            'writter'     : None,
            'running_time': None
        }
        for key, value in data.items():
            if key == '__IMAGE__':
                result['poster_url'] = value

            elif key == 'Release date(s)':
                date = value.find( 'span', { 'class': re.compile( 'published' ) } )
                if date:
                    result['release_date'] = date.string
                    result['release_year'] = int( date.string.split('-')[0] )

        return result


class Wikipedia( object ):

    FILM_SECTIONS = {
        'en': ( 'Synopsis', 'Plot', 'Plot summary' ),
        'pl': ( u'Opis fabuły', u'Zarys fabuły', u'Fabuła', ),
    }

    FILM_CATEGORY_PATTERNS = {
        'en': [ re.compile( r'(.*?)\d{4}_film(.*?)' ) ],
        'pl': [ re.compile( r'(.*?)[F|f]ilmy(.*?)' ), ]
    }

    LANG = 'en'

    @property
    def base_url( self ):
        return 'http://%s.wikipedia.org' % self.LANG

    @property
    def film_sections( self ):
        return self.FILM_SECTIONS[self.LANG]

    @property
    def film_category_patterns( self ):
        return self.FILM_CATEGORY_PATTERNS[self.LANG]

    def get_film_synopsis( self, title, year=None ):
        obj = self.search_film( title, year )
        if obj is not None:
            return self.cut_synopsis( obj['text'] )

    def cut_synopsis( self, text ):
        sections = {}
        soup = BeautifulSoup( text )
        for section in soup.findAll( 'h2' ):
            headline = section.find( 'span', { 'class': 'mw-headline' } )
            sections[strip_tags( headline or section )] = section

        for key in self.film_sections:
            if sections.has_key( key ):
                return strip_tags( sections[key].findNextSibling( 'p' ) )

        p = soup.find( 'p' )
        return strip_tags( p ) if p else None


    def get_film_info( self, title, year=None ):
        obj = self.search_film( title, year )
        if obj is not None:
            return self.parse_infobox( html=obj['text'], parser_cls=FilmInfoBoxParser )

    def search( self, phrase, limit=5 ):
        data = self.fetch_api({
            'action'  : 'query',
            'list'    : 'search',
            'srsearch':  phrase,
            'srprop'  : 'timestamp',
            'format'  : 'json',
            'limit'   : limit,
        })
        result = []
        if data.has_key( 'query' ):
            for item in data['query']['search']:
                result.append( item['title'] )
        return result

    def search_film( self, title, year=None, limit=5 ):
        query = [title]
        if year is not None:
            query.append( str( year ) )
        query.append( 'film' )
        for title in self.search( ' '.join( query ), limit ):
            content = self.get_content( title )
            if self.film_matches( content, title, year ):
                return content
        return None

    def film_matches( self, obj, title, year=None ):
        # is film ?
        if not any( [ RE_IMDB_FILM_URL.search( l ) for l in obj['externallinks'] ] ):
            if not any( [ self.is_film_category( c ) for c in obj['categories'] ] ):
                return False

        # release year matches ?
        obj['infobox'] = self.parse_infobox( html=obj['text'], parser_cls=FilmInfoBoxParser )
        obj['url'] = self.get_url( obj['title'] )
        if year is not None:
            return obj['infobox'] and obj['infobox']['release_year'] == year

        return True

    def get_url( self, title ):
        title = unicodedata.normalize( 'NFKD', title ).encode('ascii', 'ignore' ).replace( " ", "_" )
        return '%s/wiki/%s' % ( self.base_url, title )

    def is_film_category( self, category ):
        return any ( [ p.search( category ) for p in self.film_category_patterns ] )

    def get_content( self, title ):
        data = self.fetch_api({
            'action': 'parse',
            'prop'  : 'text|externallinks|categories',
            'format': 'json',
            'page'  : title,
        })
        return { 'title': title, 
                 'text': data['parse']['text']['*'], 
                 'externallinks': data['parse']['externallinks'],
                 'categories': [ c['*'] for c in data['parse']['categories']] }

    def parse_infobox( self, soup=None, html=None, parser_cls=InfoBoxParser ):
        parser = parser_cls( soup=soup, html=html )
        return parser.parse()

    def fetch_api( self, args, format='json' ):
        params = []
        for k, v in args.items():
            params.append( '%s=%s' % ( k, urllib.quote_plus( str( v ).encode( 'utf-8' ) ) ) )
        path = 'w/api.php?' + '&'.join( params )
        return getattr( self, 'fetch_%s' % format )( path )# TODO: unknown format exception

    def fetch_raw( self, path ):
        url = '%s/%s' % ( self.base_url, path )
        request = urllib2.Request( url )
        request.add_header('User-Agent', 'Mozilla/5.0')
        try:
            result = urllib2.urlopen( request )
        except urllib2.HTTPError, e:
            raise
        except urllib2.URLError, e:
            raise
        return result.read()

    def fetch_json( self, path ):
        return json.loads( self.fetch_raw( path ) )

