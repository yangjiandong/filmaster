import unittest
from film20.externallink.test_externallink import *
from film20.externallink.test_externallink_to_remove import *

def suite():
    suite = unittest.TestSuite()
    # TODO: fix these when ExternalLinks work again in 2.0 - http://jira.filmaster.org/browse/FLM-1106 
#    suite.addTest(ExternalLinkTestCase('test_save_review_link'))
#    suite.addTest(ExternalLinkTestCase('test_save_review_link_ajax'))
#    suite.addTest(ExternalLinkTestCase('test_save_video'))
#    suite.addTest(ExternalLinkTestCase('test_remove_link'))
#    suite.addTest(ExternalLinkTestCase('test_remove_link_fail'))
    suite.addTest(ExternalLinkTestCase('test_duplicate_links'))
#    suite.addTest(ExternalLinkToRemoveTestCase('test_remove_video'))
#    suite.addTest(ExternalLinkToRemoveTestCase('test_accept_remove_video'))
#    suite.addTest(ExternalLinkToRemoveTestCase('test_remove_video_with_moderation'))
    return suite
