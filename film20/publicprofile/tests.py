import unittest
from film20.publicprofile.test_request import RequestTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(RequestTestCase('test_show_article_ok'))
    suite.addTest(RequestTestCase('test_show_article_fail'))
    suite.addTest(RequestTestCase('test_show_wall_post_ok'))
    suite.addTest(RequestTestCase('test_show_wall_post_fail'))
    suite.addTest(RequestTestCase('test_show_public_profile'))
    suite.addTest(RequestTestCase('test_show_public_profile_fail'))
    suite.addTest(RequestTestCase('test_show_followed'))
    suite.addTest(RequestTestCase('test_show_followed_fail'))
    suite.addTest(RequestTestCase('test_show_followers'))
    suite.addTest(RequestTestCase('test_show_followers_fail'))
    suite.addTest(RequestTestCase('test_show_collection'))
    suite.addTest(RequestTestCase('test_show_rated_films'))
    return suite
