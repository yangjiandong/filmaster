import os
from django.conf import settings
from film20.utils.test import TestCase
from film20.search.solr_helper import is_supported

class SearchTestCase( TestCase ):
    fixtures = [ 'test_fixtures.json', ]

    def setUp( self ):
        from film20.search.solr_helper import build_daemon
        self.daemon = build_daemon()

    def _build_index( self ):
        from django.core.management import call_command
        call_command( 'update_index_queue' )

    def tearDown( self ):
        pass


