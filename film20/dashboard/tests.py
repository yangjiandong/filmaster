import unittest
from film20.dashboard.test_request import RequestTestCase
from film20.dashboard.test_download import ExportRatingsTestCase

def suite():
    suite = unittest.TestSuite()

    suite.addTest(ExportRatingsTestCase('test_build_ratings'))
    suite.addTest(ExportRatingsTestCase('test_request'))

    suite.addTest(RequestTestCase('test_get_request'))
    suite.addTest(RequestTestCase('test_post_request'))
    suite.addTest(RequestTestCase('test_post_empty_form'))
    suite.addTest(RequestTestCase('test_my_articles'))
    suite.addTest(RequestTestCase('test_show_wall_post_ok'))
    suite.addTest(RequestTestCase('test_show_wall_post_fail'))
    suite.addTest(RequestTestCase('test_save_new_article'))
    suite.addTest(RequestTestCase('test_my_recommendations'))
    return suite
