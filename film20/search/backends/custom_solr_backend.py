import socket

import logging
logger = logging.getLogger( __name__ )

from haystack.backends import log_query
from haystack.backends.solr_backend import SolrError
from haystack.backends.solr_backend import SearchQuery as SolrSearchQuery
from haystack.backends.solr_backend import SearchBackend as SolrSearchBackend

BACKEND_NAME = 'custom_solr'

class SearchBackend( SolrSearchBackend ):

    @log_query
    def search( self, *args, **kwargs ):
        return self.run_and_watch( 'search', *args, **kwargs )

    def update( self, *args, **kwargs ):
        return self.run_and_watch( 'update', *args, **kwargs )
    
    def remove(self, *args, **kwargs ):
        return self.run_and_watch( 'remove', *args, **kwargs )
    
    def clear( self, *args, **kwargs ):
        return self.run_and_watch( 'clear', *args, **kwargs )
    

    def run_and_watch( self, command, *args, **kwargs ):
        parent_command = getattr( super( SearchBackend, self ), command )
        self_command = getattr( self, command )
        please_raise = kwargs.pop( 'please_raise' ) if kwargs.has_key( 'please_raise' ) else False
        try:
            return parent_command( *args, **kwargs )
        except ( IOError, SolrError, socket.error ), e:
            if please_raise:
                raise

            from film20.search.solr_helper import build_daemon
            daemon = build_daemon()
            if not daemon.is_active():
                logger.info( "Ups, solr is probably dead restarting ..." )
                daemon.restart( force=True)
                kwargs['please_raise'] = True
                return self_command( *args, **kwargs )


class SearchQuery( SolrSearchQuery ):

    def __init__( self, site=None, backend=None ):
        super( SearchQuery, self ).__init__( site, backend )
        self.backend = backend or SearchBackend( site=site )

