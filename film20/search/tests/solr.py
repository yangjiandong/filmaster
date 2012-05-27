from django.utils import unittest
from django.conf import settings
from haystack.query import SearchQuerySet

from film20.utils.test import TestCase
from film20.search.tests.base import SearchTestCase, is_supported

@unittest.skipIf( not is_supported(), "search tests only runs when solr is supported" )
class SolrTestCase( SearchTestCase ):

    def tearDown( self ):
        self.daemon.stop()

    def testStart( self ):
        self.daemon.start()

        self.assertTrue( self.daemon.is_runing() )
        self.assertTrue( self.daemon.is_active() )

    def testStop( self ):
        self.testStart()
        self.daemon.stop()

        self.assertFalse( self.daemon.is_runing() )
        self.assertFalse( self.daemon.is_active() )

    def testRestart( self ):
        self.daemon.restart()

        self.assertTrue( self.daemon.is_runing() )
        self.assertTrue( self.daemon.is_active() )

    def testAutoStart( self ):
        self.testStart()
        self._build_index()
        self.testStop()

        sqs = SearchQuerySet()
        sqs = sqs.filter( title="Godfather" )
        self.assertEqual( sqs.count(), 2 )
        
        self.assertTrue( self.daemon.is_runing() )
        self.assertTrue( self.daemon.is_active() )


