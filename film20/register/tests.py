import unittest
from film20.utils.test import TestCase
from django.contrib.auth.models import User
from film20.config.urls import *
from film20.register.models import RegistrationModel

class RegisterTestCase(TestCase):

    u1 = None

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

    def clean_data(self):
        User.objects.all().delete()
        RegistrationModel.objects.all().delete()
        
    def test_user_authenticated(self):

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        register_form_url = "/"+urls["MOBILE"]+"/"

        data = {
            'email' : "borys.musielak@gmail.com",
            'opinion' : 1,
        }

        response = self.client.post(
                        register_form_url,
                        data,
                   )
        # there should be only one registration model
        self.failUnlessEqual(len(RegistrationModel.objects.all()), 1)

        # checking if relation to user is saved
        reg = RegistrationModel.objects.get(user__username="michuk")
        self.failUnlessEqual(reg.user.username, self.u1.username)
        self.failUnlessEqual(reg.opinion, 1)

    def test_user_notauthenticated(self):

        self.initialize()

        register_form_url = "/"+urls["MOBILE"]+"/"

        data = {
            'email' : "borys.musielak@gmail.com",
            'opinion' : 1,
            'beta_code': "antyweb"
        }

        response = self.client.post(
                        register_form_url,
                        data,
                   )
        # there should be only one registration model
        self.failUnlessEqual(len(RegistrationModel.objects.all()), 1)
        reg = RegistrationModel.objects.all()
        reg = reg[0]
        # checking if relation to user is saved
        self.failUnlessEqual(reg.user is None, True)
        self.failUnlessEqual(reg.opinion, 1)
        self.failUnlessEqual(reg.beta_code, "antyweb")

def suite():
    suite = unittest.TestSuite()
#    suite.addTest(RegisterTestCase('test_user_authenticated')) # TODO: fix in http://jira.filmaster.org/browse/FLM-1124 
#    suite.addTest(RegisterTestCase('test_user_notauthenticated')) # TODO: fix in http://jira.filmaster.org/browse/FLM-1124
    return suite
