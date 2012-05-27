from film20.utils.test import TestCase
from django.contrib.auth.models import User
from film20.core.models import Film, Object
from film20.blog.models import Post
from film20.config.urls import *
from film20.utils.utils import proccess_json_response

class SuperFormTestCase(TestCase):

    u1 = None
    film = None

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save()

    def clean_data(self):
        User.objects.all().delete()
        Post.objects.all().delete()

    def test_super_form(self):

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        super_form_url = "/"+urls["SUPER_FORM_ADD_NOTE"]+"/"

        data = {
            'body' : "Lorem ipsum!",
            'related_film' : self.film.title,
        }

        response = self.client.post(
                        super_form_url,
                        data,
                   )
        self.failUnlessEqual(len(Post.objects.all()), 1)


    def test_super_form_ajax(self):

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        super_form_url = "/"+urls["SUPER_FORM_ADD_NOTE"]+"/json/"

        data = {
            'body' : "Lorem ipsum!",
            'related_film' : self.film.title,
        }

        response = self.client.post(
                        super_form_url,
                        data,
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                   )
        data, success = proccess_json_response(response.content)

        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(success, "true")

        response = self.client.get('/note-partial/'+data+'/',
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.failUnlessEqual(response.status_code, 200)
