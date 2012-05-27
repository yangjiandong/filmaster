import unittest
from film20.followers.test_followers import FollowersTestCase

def suite():
    suite = unittest.TestSuite()

    suite.addTest(FollowersTestCase('test_follow'))
    suite.addTest(FollowersTestCase('test_followers'))
    suite.addTest(FollowersTestCase('test_block'))
    suite.addTest(FollowersTestCase('test_blockers'))
    suite.addTest(FollowersTestCase('test_remove'))
    suite.addTest(FollowersTestCase('test_friends'))
    suite.addTest(FollowersTestCase('test_relation'))
    suite.addTest(FollowersTestCase('test_notification'))
    suite.addTest(FollowersTestCase('test_follow_on_create'))
    suite.addTest(FollowersTestCase('test_follow_command'))
    return suite
