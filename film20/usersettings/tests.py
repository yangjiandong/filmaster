from django.utils import unittest
from film20.usersettings.test_request import *
from film20.usersettings.test_avatars import AvatarTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(RequestTestCase('test_edit_notification_settings'))
    suite.addTest(RequestTestCase('test_import_ratings'))
    suite.addTest(RequestTestCase('test_password_change'))
    suite.addTest(RequestTestCase('test_change_display_name'))
    
    suite.addTest(AvatarTestCase('test_avatar_caching'))
    suite.addTest(AvatarTestCase('test_no_avatar_in_storage'))

    return suite

