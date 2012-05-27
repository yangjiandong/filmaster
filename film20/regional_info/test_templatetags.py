import unittest

from django.contrib.auth.models import User

from film20.regional_info.models import RegionalInfo
from film20.regional_info.templatetags.regional_info import get_regional_info_obj
from film20.utils.test import TestCase

class TemplatetagsTestCase(TestCase):

    def initialize(self):
        self.clean_data()
        
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        ri = RegionalInfo()
        ri.user = self.u1
        ri.town = "warsaw"
        ri.region = "mazowieckie"
        ri.contents = "Lorem ipsum"
        ri.save()

    def clean_data(self):
        RegionalInfo.objects.all().delete()
        User.objects.all().delete()

    def test_get_regional_info_obj(self):
        """
            Test get_regional_info_obj - should return
            regional info object for given city and region
        """
        self.initialize()

        obj = get_regional_info_obj("warsaw", "mazowieckie")

        self.failUnlessEqual(obj.contents, "Lorem ipsum")

    def test_get_regional_info_obj_fail(self):
        """
            Test get_regional_info_obj - should return
            None
        """
        self.initialize()

        obj = get_regional_info_obj("gdansk", "pomorskie")

        self.failUnlessEqual(obj, None)

