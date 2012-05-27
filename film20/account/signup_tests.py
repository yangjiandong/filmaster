# -!- coding: utf-8 -!-
from film20.utils.test import TestCase
from film20.config.urls import *
from film20.account.forms import SignupForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class SignupTestCase(TestCase):

    def initialize(self):
        self.clean_data()

    def clean_data(self):
        User.objects.all().delete()

    def test_signup_form(self):
        from .forms import SSORegistrationForm

        form = SSORegistrationForm(dict(username=u'user-name', email='some@email.pl'))
        self.assertFalse(form.is_valid())

        form = SSORegistrationForm(initial=dict(username=u'ĄĆĘÓŁŃŚŹŻ ąćęółńśźż', email='some@email.pl'))
        self.assertTrue('ACEOLNSZZaceolnszz' in unicode(form['username']))
        return form

    def test_signup_all_valid(self):
        """
            Everything in the signup form is valid
        """
        self.initialize()

        register_form_url = "/"+urls["REGISTRATION"]+"/"

        data = {
            'username':"michuk",
            'password1':"dupa.8",
            'password2':"dupa.8",
            'email':'michuk@michuk.michuk',
            'inform_friends': 'on',
        }

        response = self.client.post(
                        register_form_url,
                        data,
                   )
       
        # if the form is valid user is redirected to dashboard page
        self.failUnlessEqual(response.status_code, 302)

        users = User.objects.all()

        # there should be one user in database
        self.failUnlessEqual(users.count(), 1)

        # and his name is michuk
        self.failUnlessEqual(users[0].username, "michuk")
        
        settings = self.get_notice_settings(users[0])
        self.assertTrue(settings)
        self.assertTrue(any(s.send for s in settings))
    
    def test_signup_disable_notifications(self):
        self.initialize()

        register_form_url = "/"+urls["REGISTRATION"]+"/"

        data = {
            'username':"michuk",
            'password1':"dupa.8",
            'password2':"dupa.8",
            'email':'michuk@michuk.michuk',
            'inform_friends': '',
            'answer':"5",
        }

        response = self.client.post(
                        register_form_url,
                        data,
                   )
        
        user = User.objects.get(username='michuk')
        
        settings = self.get_notice_settings(user)

        self.assertTrue(settings)
        self.assertFalse(any(s.send for s in settings))

    def get_notice_settings(self, user):
        from film20.notification import models as notification
        from film20.notification.models import NoticeType
        
        settings = []
        notice_types = NoticeType.objects.filter(type=NoticeType.TYPE_USER_ACTIVITY)
        for notice_type in notice_types:
            for medium in notification.NOTICE_MEDIA:
                if medium.supports(notice_type):
                    settings.append(medium.get_notification_setting(user, notice_type))
        return settings

    def test_signup_wrong_answer(self):

        """
            Wrong answer in signup form
        """
        
        self.initialize()

        register_form_url = "/"+urls["REGISTRATION"]+"/"

        data = {
            'username':"michuk",
            'password1':"dupa.8",
            'password2':"dupa.8",
            'email' : 'michuk@michuk.michuk',
            'answer':"viagra!!",
            'inform_friends': 'on',
        }

        response = self.client.post(
                        register_form_url,
                        data,
                   )

        # if the form is valid user is redirected to dashboard page
        self.failUnlessEqual(response.status_code, 200)

        users = User.objects.all()

        # there are no users in database
        self.failUnlessEqual(users.count(), 0)

    def test_signup_email_validation( self ):

        # add user
        self.test_signup_all_valid()
        
        # email should be saved after registration
        users = User.objects.all()

        self.failUnlessEqual( users.count(), 1 )
        self.assertEqual( users[0].email, "michuk@michuk.michuk" ) 

        # try to register another user with same email
        register_form_url = "/"+urls["REGISTRATION"]+"/"

        data = {
            'username':"michuk2",
            'password1':"dupa.8",
            'password2':"dupa.8",
            'email':'michuk@michuk.michuk',
            'inform_friends': 'on',
        }

        response = self.client.post( register_form_url, data )
        
        # email validation error should be raised
        self.failUnlessEqual( response.status_code, 200 )
        self.assertFormError( response, 'form', 'email', _( "That email address is already taken. Please choose another." ) )

