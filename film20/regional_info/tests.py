import unittest
from film20.regional_info.test_templatetags import TemplatetagsTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TemplatetagsTestCase('test_get_regional_info_obj'))
    suite.addTest(TemplatetagsTestCase('test_get_regional_info_obj_fail'))
    return suite