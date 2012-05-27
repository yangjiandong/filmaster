import os

from django.test.client import Client
from django.utils import unittest

from film20.core.models import Rating
from film20.core.models import Film
from film20.core.models import User
from film20.import_ratings.models import save_ratings_in_db
from film20.import_ratings.import_ratings_helper import *
from film20.import_ratings.tests.imports import ImportTestCase
from film20.utils.test import integration_test

class CritickerImportTestCase(ImportTestCase):

    @integration_test
    def test_import(self):
        """
            Import a sample voting history from Criticker XML file
        """
        path = os.path.dirname('')
        vote_history = os.path.abspath(
                    'import_ratings/tests/test_data/criticker_rankings.xml')

        ratings_list = parse_criticker_votes(vote_history)
        self.assertEquals(len(ratings_list), 10)

        save_ratings_in_db(self.u1, ratings_list, ImportRatings.CRITICKER, 
                        overwrite=True)

        all_ratings = ImportRatings.objects.all()
        self.assertEquals(len(all_ratings), 1)

        """
            Gets the import records stored in ImportRatings table and
            imports them into single Rating records
        """

        import_ratings()

        ratingsLogs = ImportRatingsLog.objects.all()
        self.assertEquals(len(ratingsLogs), 1)

        ratings = Rating.objects.all()
        self.assertEquals(len(ratings), 10)
