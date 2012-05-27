from film20.utils.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.usersettings.views import *
from film20.config.urls import *
from film20.core.models import Profile

import logging
logger = logging.getLogger(__name__)

class RequestTestCase(TestCase):

    def setUp(self):
        User.objects.all().delete()

        # set up users
        self.u1 = User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')        
        self.u2 = User.objects.create_user('adz', 'adz@gmail.com', 'secret')

    def test_edit_notification_settings(self):
        """
            Basic test for edit_notification_settings view
        """
        self.client.login(username=self.u1.username, password='secret')
        response = self.client.get('/'+urls["SETTINGS"]+'/'+urls["MANAGE_NOTIFICATIONS"]+'/')
        self.failUnlessEqual(response.status_code, 200)


    def test_import_ratings(self):
        """
            Basic test for test_import_ratings view
        """
        self.client.login(username=self.u1.username, password='secret')
        response = self.client.get('/'+urls["SETTINGS"]+'/'+urls["IMPORT_RATINGS"]+'/')
        self.failUnlessEqual(response.status_code, 200)

    def test_password_change(self):
        """
            Basic test for password_change view
        """
        def fetch(user):
            return user.__class__.objects.get(username=user.username)

        self.assertFalse(self.client.login(username=self.u1.username, password='invalidpass'))
        self.assertTrue(self.client.login(username=self.u1.username, password='secret'))

        self.u1.set_unusable_password()
        self.u1.save()

        view = reverse("change_password")

        self.client.post(view, {'password1':'dupa', 'password2': 'blada'})
        
        self.assertFalse(fetch(self.u1).has_usable_password())
        
        self.client.post(view, {'password1':'dupa.8', 'password2': 'dupa.8'})

        self.assertTrue(fetch(self.u1).check_password('dupa.8'))
        
        self.client.post(view, {'oldpassword':'bad', 'password1':'nicepwd', 'password2': 'nicepwd'})
        self.assertFalse(fetch(self.u1).check_password('nicepwd'))

        self.client.post(view, {'oldpassword':'dupa.8', 'password1':'nicepwd', 'password2': 'nicepwd'})
        self.assertTrue(fetch(self.u1).check_password('nicepwd'))
        
    def test_change_display_name(self):
        self.assertTrue(self.client.login(username=self.u1.username, password='secret'))
        view = reverse("edit_profile")

        # display_name not changed because we have other user with the same username
        self.client.post(view, {'display_name':'adz'})
        
        michuk_profile = Profile.objects.get(user=self.u1)
        self.assertEquals(michuk_profile.get_current_display_name(), 'michuk')

        # display_name changed!
        self.client.post(view, {'display_name':'michuk2'})
        
        michuk_profile = Profile.objects.get(user=self.u1)
        self.assertEquals(michuk_profile.get_current_display_name(), 'michuk2')
        
    def tearDown(self):
        User.objects.all().delete()
        