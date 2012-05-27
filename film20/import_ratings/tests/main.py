from django.core import mail

from film20.core.models import Rating
from film20.core.models import Film
from film20.core.models import User

from film20.import_ratings.models import ImportRatings, ImportRatingsLog
from film20.import_ratings.import_ratings_helper import import_ratings
from film20.import_ratings.tests.imports import ImportTestCase

from film20.utils.test import integration_test

class ImportRatingsTestCase( ImportTestCase ):

    @integration_test
    def test_import_errors( self ):

        mail.outbox = []
        
        # importratings broken json string
        ir = ImportRatings( user=self.u1, kind=ImportRatings.IMDB, movies = "{[#ups we have problem" )
        ir.save()

        # 1 .. 2 .. 3 .. attempt
        ir = ImportRatings.objects.get( pk=ir.pk )
        self.assertEqual( ir.attempts, 3 )
        self.assertEqual( ir.import_status, ImportRatings.STATUS_IMPORT_FAILED )
        self.assertFalse( ir.import_error_message is None )
        self.assertFalse( ir.is_imported )
    
        self.assertEqual( len( mail.outbox ), 1 )

        # after manually fix
        ir.movies = '[{"title": "Wristcutters: A Love Story", "year": 2006, "score": 7, "imdb_id": "0477139"}]'
        ir.attempts = 0
        ir.import_error_message = None
        ir.import_status = ImportRatings.STATUS_UNKNOWN
        ir.save()

        ir = ImportRatings.objects.get( pk=ir.pk )
        self.assertEqual( ir.attempts, 1 )
        self.assertEqual( ir.import_status, ImportRatings.STATUS_UNKNOWN )
        self.assertTrue( ir.import_error_message is None )
        self.assertTrue( ir.is_imported )
    
        self.assertEqual( len( mail.outbox ), 2 )

