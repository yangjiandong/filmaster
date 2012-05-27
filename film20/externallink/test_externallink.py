from film20.utils.test import TestCase

from film20.externallink.models import *
from film20.utils.utils import proccess_json_response

class ExternalLinkTestCase(TestCase):

    u1 = None

    link = None

    film = None

    def clean_data(self):
        User.objects.all().delete()
        ExternalLink.objects.all().delete()

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.is_superuser = True
        self.u1.save()
        self.u2 = User.objects.create_user('adz', 'b.orysmusielak@gmail.com', 'secret')
        self.u2.save()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save()

        # set up links
        self.link = ExternalLink()
        self.link.url = "http://www.youtube.com/watch?v=h0R_FR9pD2k"
        self.link.url_kind = ExternalLink.TRAILER
        self.link.user = self.u1
        self.link.film = self.film
        self.link.type = Object.TYPE_LINK
        self.link.permalink = "LINK"
        self.link.save()

    def test_save_review_link(self):
        """
           Test saving review link
        """

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        # sending link
        add_link_url = "/"+urls["FILM"]+"/"+self.film.permalink+"/"+urls["ADD_LINKS"]+"/"

        data = {
            'title' : "test review",
            'excerpt' : "Lorem ipsum!",
            'url' : "http://osnews.pl",
            'url_kind' : ExternalLink.REVIEW
        }

        response = self.client.post(
                            add_link_url,
                            data,
                       )

        self.failUnlessEqual(response.status_code, 200)

    def test_save_review_link_ajax(self):
        """
            Test saving review link with ajax
        """

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        # sending link
        add_link_url = "/"+urls["FILM"]+"/"+self.film.permalink+"/"+urls["ADD_LINKS"]+"/json/"

        data = {
            'title' : "test review",
            'excerpt' : "Lorem ipsum!",
            'url' : "http://osnews.pl",
            'url_kind' : ExternalLink.REVIEW
        }

        response = self.client.post(
                        add_link_url,
                        data,
                        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                   )

        data, success = proccess_json_response(response.content)

        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(success, "true")

        # if link was saved getting it from db
        response = self.client.get('/partial_link/'+data+'/',
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.failUnlessEqual(response.status_code, 200)

    def test_save_video(self):
        """
           Test saving video
        """

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        # sending video
        add_video_url = "/"+urls["FILM"]+"/"+self.film.permalink+"/"+urls["ADD_VIDEO"]+"/"

        data = {
            'url' : "http://www.youtube.com/watch?v=h0R_FR9pD2k",
            'url_kind' : ExternalLink.TRAILER
        }

        response = self.client.post(
                        add_video_url,
                        data,
                   )

        # status code 302 because if video is added to db user is redirected to film page
        self.failUnlessEqual(response.status_code, 302)

    def test_remove_link_fail(self):
        """
           Test delete feature with fail
        """

        self.initialize()

        self.client.login(username=self.u2.username, password='secret')

        remove_video_url = "/"+urls["FILM"]+'/'+self.film.permalink+'/'+urls["REMOVE_LINKS"]+'/'+str(self.link.id)+'/'

        response = self.client.get(remove_video_url)

        # status code 302 because if link is removed user is redirected to add link page
        self.failUnlessEqual(response.status_code, 302)
        link = ExternalLink.objects.get(id=self.link.id)
        # link is not removed because it was created by u1 and u2 is trying to remove it!
        self.failUnlessEqual(link.status, ExternalLink.PUBLIC_STATUS)

    def test_remove_link(self):
        """
           Test delete feature
        """

        self.initialize()

        self.client.login(username=self.u1.username, password='secret')

        remove_video_url = "/"+urls["FILM"]+'/'+self.film.permalink+'/'+urls["REMOVE_LINKS"]+'/'+str(self.link.id)+'/'

        response = self.client.get(remove_video_url)

        # status code 302 because if link is removed user is redirected to add link page
        self.failUnlessEqual(response.status_code, 302)
        link = ExternalLink.objects.get(id=self.link.id)
        # link is removed
        self.failUnlessEqual(link.status, ExternalLink.DELETED_STATUS)


    def test_duplicate_links( self ):

        self.initialize()

        e1 = ExternalLink( user=self.u1, film=self.film, permalink='LINK', version=1,
                            type=ExternalLink.TYPE_LINK, status=ExternalLink.PUBLIC_STATUS,
                                url_kind = ExternalLink.TRAILER, url="http://yt.com" )
        e1.save()

        self.assertEqual( ExternalLink.objects.count(), 2 )

        e2 = ExternalLink( user=self.u1, film=self.film, permalink='LINK', version=1,
                            type=ExternalLink.TYPE_LINK, status=ExternalLink.PUBLIC_STATUS,
                                url_kind = ExternalLink.TRAILER, url="http://yt.com/2" )
        e2.save()

        self.assertEqual( ExternalLink.objects.count(), 3 )

        try:
            e3 = ExternalLink( user=self.u1, film=self.film, permalink='LINK', version=1,
                                type=ExternalLink.TYPE_LINK, status=ExternalLink.PUBLIC_STATUS,
                                    url_kind = ExternalLink.TRAILER, url="http://yt.com/2" )
            e3.save()

        except Exception:
            from django.db import connection
            connection.close()

        else:
            self.fail()
