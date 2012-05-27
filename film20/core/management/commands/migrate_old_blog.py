# -*- coding: utf-8 -*-

import os
import re
import urllib
import urllib2
import datetime
import BeautifulSoup
import htmlentitydefs

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from film20.blog.models import Post

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text.encode( 'utf-8' ) )

class BasePost( object ):
    def __init__( self, url, title, date, tags, content ):
        self.url = url
        self.title = unescape( title )
        self.date = date
        self.tags = unescape( tags )
        self.content = unescape( content )

    def __str__( self ):
        return "%s:%s" % ( self.title, self.date )

class Fetcher( object ):
    def __init__( self, url ):
        self.url = url
        self.posts = []

    def fetch_posts( self, page=1 ):
        url = '%s/page/%d/' % ( self.url, page )
        print " -- fetching from %s" % url
        content = urllib2.urlopen( url ).read()
        soup = BeautifulSoup.BeautifulSoup( content )

        posts = soup.findAll( 'div', { 'class': 'bpost' } )
        for post in posts:
            p = BasePost(
                url = self._get_url( post ),
                title = self._get_title( post ),
                date = self._get_date( post ),
                tags = self._get_tags( post ),
                content = self._get_content( post )
            )
            print " --- ", p
            self.posts.append( p )

        if len( posts ):
            self.fetch_posts( page+1 )

    @property
    def month_names( self ):
        if self.url.endswith( 'pl' ):
            return [ 'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec', 'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień' ]
        return [ 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December' ]

    def _get_url( self, post ):
        return post.h2.a['href']

    def _get_title( self, post ):
        return ''.join( [ str( t ) for t in post.h2.a.contents ] )

    def _get_tags( self, post ):
        tags = []
        for tag in post.findAll( 'a', { 'rel': 'tag' } ):
            tags.append( tag.string )
        return ','.join( tags )

    def _get_date( self, post ):
        t = post.find( 'div', { 'class': 'btags' } ) 
        if t is None: # filmaster.com
            t = post.find( 'div', { 'class': 'tags' } )
        m = re.match( ".*@(.*)", t.contents[-1] )
        s = "%s %s" % ( post.findPreviousSibling( 'h4' ).string, m.group(1).strip() )
        n = 1
        for month in self.month_names:
            s = s.replace( month, str( n ) )
            n += 1
        return datetime.datetime.strptime( s, "%m %d, %Y %I:%M %p" )

    def _get_content( self, post ):
        url = self._get_url( post )
        print "  -- fetching content %s" % url
        content = urllib2.urlopen( url ).read()
        soup = BeautifulSoup.BeautifulSoup( content )
        content = soup.find( 'div', { 'class': 'entry' } )

        # remove comments
        for comment in content.findAll( text=lambda text: isinstance( text, BeautifulSoup.Comment ) ):
            comment.extract()

        # ... and facebook like
        for fb in content.findAll( 'iframe', { 'src': re.compile( "http://www.facebook.com/plugins.like.php" ) } ):
            fb.hidden = True

        # also migrate images
        for image in content.findAll( 'img', { 'src': re.compile( "http://blog.filmaster" ) } ):
            filename = image['src'].split( "/" )[-1]
            out = 'static/uploads/b/oldblog-%s' % filename
            if not os.path.exists( 'static/uploads/b' ):
                os.mkdir( 'static/uploads/b' )
            if not os.path.exists( out ):
                urllib.urlretrieve( image['src'], out )
            image['src'] = "/%s" % out

        return content.renderContents()

class Command( BaseCommand ):
    help = 'Migrates old blog.filmaster.[pl|com] posts to user blog'

    def handle( self, *args, **options ):
        fetcher = Fetcher( '%s' % settings.BLOG_DOMAIN )
        fetcher.fetch_posts()

        print " ++ %d POSTS TO SAVE ++" % len( fetcher.posts )
        user, created = User.objects.get_or_create( username="blog" )
        for p in fetcher.posts:
            print " + saving post: %s" % p
            try:
                Post.objects.get( user=user, title=p.title, LANG=settings.LANGUAGE_CODE )
                print "  - already exists [SKIPING]"
            except Post.DoesNotExist:
                post = Post(
                    title = p.title,
                    user = user,
                    body = p.content,
                    publish = p.date,
                    is_public = True,
                    is_published = True,
                    tag_list = p.tags
                )
                post.save( permalink=p.url.split( '/' )[-1] )
