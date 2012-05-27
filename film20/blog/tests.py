import unittest

# Project
from film20.blog.post_tests import PostTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(PostTestCase('test_edit_existing_post'))
    suite.addTest(PostTestCase('test_edit_deleted_post'))
    suite.addTest(PostTestCase('test_all_for_user'))
    suite.addTest(PostTestCase('test_public_for_user'))
    suite.addTest(PostTestCase('test_empty_page_response'))
    suite.addTest(PostTestCase('test_cache_recent_reviews'))
    suite.addTest(PostTestCase('test_cache_featured_review'))
    suite.addTest(PostTestCase('test_tagging'))
    suite.addTest(PostTestCase('test_related_movies'))
    return suite
