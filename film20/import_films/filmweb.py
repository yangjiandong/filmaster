# -*- coding: utf-8 -*-

import logging, urllib2, urllib, re
from BeautifulSoup import BeautifulSoup

def remove_html_tags( text ):
    p = re.compile( r'<.*?>' )
    return p.sub( '', text )

def remove_extra_spaces( text ):
    return ' '.join( text.split() )

def empty( text ):
    return text is None or re.match( '^\s*$', text )


class Person:
    name_surname = url = None

class Actor( Person ):
    role = None

    def __str__( self ):
        return '%s [%s] - %s' % ( self.name_surname, self.url, self.role )

class Movie:
    str = """
+--------
| Tytuł           : %s, (%s)
| Rok produkcji   : %s
| Reżyser         : %s
| Scenariusz      : %s
| Kraj            : %s
| Gatunek         : %s
+--------
"""
    directors = writers = countries = type = None
    actors = []
    def __str__( self ):
        return self.str % ( self.pl_title, self.org_title, self.year, self.directors, self.writers, self.countries, self.type )

class Filmweb:
    BASE_URL = 'http://www.filmweb.pl'

    def __init__( self ):
        self.opener = urllib2.build_opener()

    def searchMovieByTitle( self, title ):
        result = []

        params = urllib.urlencode( { 'q': title, 'alias': 'film' } )
        response = self.opener.open( "%s/search?%s" % ( self.BASE_URL, params ) )

        soup = BeautifulSoup( response.read() )
        items = soup.findAll( 'li', { 'class': 'searchResult HorListItem' } )
        for item in items:

            movie = Movie()
            movie.pl_title, movie.org_title = self.__extractTitle( str( item.h3.a ) )
            movie.url = self.BASE_URL + item.h3.a['href']
            movie.year = self.__extractYear( str( item.find( 'span', { 'class': 'searchResultDetails' } ) ) )

            result.append( movie )

        return result

    def getMovieByTitle( self, title, year ):
        movies = self.searchMovieByTitle( title )
        for m in movies:
            if m.year == year:
                return self.getMovieByURL( m.url )
        return None

    def getMovieByURL( self, url ):
        movie = Movie()

        response = self.opener.open( url )
        soup = BeautifulSoup( response.read() )
        basicInfo = soup.find( 'div', { 'class': 'basic-info-wrapper' } ).findAll( 'tr' )

        elements = {}
        for item in basicInfo:
            role = item.th.string.replace( ':', '' )
            value = []
            for v in item.td.contents:
                value.append( v.string )
                elements[role] = remove_extra_spaces( ' '.join( value ) )

        mainInfo = soup.find( 'h1', { 'class': 'pageTitle item' } )
        orgInfo = soup.find( 'h2', { 'class': 'original-title' } )

        movie.url = self.BASE_URL + mainInfo.a['href']
        movie.year = orgInfo.span.string

        # TODO find better way to do this
        movie.pl_title = mainInfo.a.contents[1]
        movie.org_title = remove_extra_spaces( orgInfo.contents[2] )
        if empty( movie.org_title ):
            movie.org_title = movie.pl_title

        # TODO to Person class
        movie.directors = elements[ unicode( 'reżyseria' ) ]
        movie.writers = elements[ unicode( 'scenariusz' ) ]

        movie.countries = elements[ unicode( 'produkcja' ) ]
        movie.type = elements[ unicode( 'gatunek' ) ]
        movie.release = elements[ unicode( 'premiera' ) ]

        movie.actors = self.getMovieActors( movie )

        return movie

    def getMovieActors( self, movie ):
        actors = []

        response = self.opener.open( '%s/cast' % movie.url )
        soup = BeautifulSoup( response.read() )

        dd = soup.find( id='role-actors' ).nextSibling.nextSibling
        items = dd.findAll( 'li', { 'class': 'clear_li' } )
        for item in items:
            actor = Actor()
            actor.url = self.BASE_URL + item.h3.a['href']
            actor.name_surname =  item.h3.a.findAll( 'span' )[1].string
            actor.role = remove_extra_spaces( item.div.string ) if not empty( item.div.string ) else None

            actors.append( actor )

        return actors

    def getUserRatings( self, username ):
        pass

    def getUserFilmRating( self, username, title, year ):
        pass

    def __extractTitle( self, content ):
        content = remove_html_tags( content )
        m1 = re.match( r'(.*)/(.*)', content )
        if m1 is not None:
            return remove_extra_spaces( m1.group(1) ), remove_extra_spaces( m1.group(2) )
        else:
            c = remove_extra_spaces( content )
            return c, c

    def __extractYear( self, content ):
        content = remove_extra_spaces( remove_html_tags( content ) )
        m1 = re.match( r'(\d{4})', content )
        return m1.group( 1 )


if __name__ == '__main__':
    filmweb = Filmweb()
    movies = [
        filmweb.getMovieByTitle( 'Labirynt Fauna', '2006' ),
        filmweb.getMovieByTitle( 'The Others', '2001' ),
        filmweb.getMovieByTitle( '[REC]', '2007' ),
        filmweb.getMovieByTitle( 'Aspen Extreme', '1993' ),
        filmweb.getMovieByTitle( 'Forrest Gump', '1994' ),
        filmweb.getMovieByTitle( 'Iron Man 2', '2010' ),
        filmweb.getMovieByTitle( 'Pianista', '2002' ),
    ]

    for m in movies:
        if m is not None:
            print '%s\n Aktorzy:\n' % m
            for a in m.actors:
                print '  --- %s' % a

#vim: fdm=marker ts=4 sw=4 sts=4
