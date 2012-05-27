import unittest
from film20.threadedcomments.test_threadedcomments import *

def suite():
    suite = unittest.TestSuite()
    suite.addTest(ThreadedCommentTestCase('test_comments'))
    suite.addTest(ThreadedCommentTestCase('test_comment_delete'))
    suite.addTest(ThreadedCommentTestCase('test_comments_ajax'))
    return suite
