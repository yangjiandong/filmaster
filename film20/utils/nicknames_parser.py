# based on http://raw.github.com/BonsaiDen/twitter-text-python

import re
import urllib

from film20.core.templatetags.map_url import url_username_link

AT_SIGNS = ur'[@\uff20]'
LIST_END_CHARS = ur'([a-z0-9_]{1,20})(/[a-z][a-z0-9\x80-\xFF-]{0,79})?'
USERNAME_REGEX = re.compile( ur'\B' + AT_SIGNS + LIST_END_CHARS, re.IGNORECASE )

class NicknamesParser( object ):
    
    def __init__( self ):
        self.usernames = []

    def parse( self, text ):
        return USERNAME_REGEX.sub( self._parse_nicknames, text )

    def _parse_nicknames( self, match ):
        if match.group( 2 ) is not None:
            return match.group( 0 )
        
        mat = match.group( 0 )
        self.usernames.append( mat[1:] )
        
        return self.format_username( mat[0:1], mat[1:] )
  
    def format_username( self, at_char, username ):
        return '<a href="%s" rel="nofollow">%s%s</a>' % ( url_username_link( username ), at_char, username )
