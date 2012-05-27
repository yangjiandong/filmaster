from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission

from film20.utils.test import TestCase
from film20.core.models import Film, Object
from film20.externallink.models import ExternalLink, ExternalLinkToRemove, moderated_links_to_remove

class ExternalLinkToRemoveTestCase( TestCase ):
    
    def setUp( self ):
        # test user with no permissions
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )
        
        # test user with moderation_permission
        self.u2 = User.objects.create_user( "root", "root@root.com", "root" )
        self.u2.user_permissions.add( Permission.objects.get( codename="can_add_link" ) )
        self.u2.save()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save()

        # set up links
        self.link1 = ExternalLink( user=self.u2, film=self.film, permalink='LINK', version=1,
                            type=ExternalLink.TYPE_LINK, status=ExternalLink.PUBLIC_STATUS,
                                url_kind = ExternalLink.TRAILER, url="http://yt.com" )

        self.link2 = ExternalLink( user=self.u2, film=self.film, permalink='LINK', version=1,
                            type=ExternalLink.TYPE_LINK, status=ExternalLink.PUBLIC_STATUS,
                                url_kind = ExternalLink.TRAILER, url="http://yt.com/v=1" )
        self.link1.save()
        self.link2.save()


    def tearDown( self ):

        mail.outbox = []

        User.objects.all().delete()
        Film.objects.all().delete()
        ExternalLink.objects.all().delete()
        ExternalLinkToRemove.objects.all().delete()
    
    def test_remove_video( self ):
        
        self.client.login( username='root', password='root' )
        response = self.client.get( reverse( 'remove-video', args=( self.link1.pk, ) ) )
        self.assertEqual( response.status_code, 302 )

        self.assertEqual( ExternalLink.objects.count(), 1 )
        self.assertEqual( ExternalLinkToRemove.objects.count(), 0 )

    def test_remove_video_with_moderation( self ):
        
        self.client.login( username='user', password='user' )
        response = self.client.get( reverse( 'remove-video', args=( self.link1.pk, ) ) )
        self.assertEqual( response.status_code, 302 )

        self.assertEqual( ExternalLink.objects.count(), 2 )
        self.assertEqual( ExternalLinkToRemove.objects.count(), 1 )

        link_to_remove = ExternalLinkToRemove.objects.all()[0]
        self.assertEqual( link_to_remove.moderation_status, ExternalLinkToRemove.STATUS_UNKNOWN )

        reason = "Trailer is ok."
        self.client.login( username='root', password='root' )
        response = self.client.post( reverse( 'moderate-item', args=( moderated_links_to_remove.get_name(),) ), 
                                                { "id": link_to_remove.pk, "reject": "1", "confirmed": "1", "reason": reason })


        link_to_remove = ExternalLinkToRemove.objects.all()[0]

        self.assertEqual( link_to_remove.moderation_status, ExternalLinkToRemove.STATUS_REJECTED )
        self.assertEqual( link_to_remove.rejection_reason, reason )

        self.assertEqual( len( mail.outbox ), 1 )

        print mail.outbox[0].body

        self.assertTrue( reason in mail.outbox[0].body )
        self.assertTrue( self.film.get_absolute_url() in mail.outbox[0].body )

    def test_accept_remove_video( self ):
        
        self.client.login( username='user', password='user' )
        response = self.client.get( reverse( 'remove-video', args=( self.link1.pk, ) ) )
        self.assertEqual( response.status_code, 302 )

        self.assertEqual( ExternalLink.objects.count(), 2 )
        self.assertEqual( ExternalLinkToRemove.objects.count(), 1 )

        link_to_remove = ExternalLinkToRemove.objects.all()[0]
        self.assertEqual( link_to_remove.moderation_status, ExternalLinkToRemove.STATUS_UNKNOWN )

        self.client.login( username='root', password='root' )
        response = self.client.post( reverse( 'moderate-item', args=( moderated_links_to_remove.get_name(),) ), 
                                                { "id": link_to_remove.pk, "accept": "1" })


        self.assertEqual( ExternalLink.objects.count(), 1 )
        self.assertEqual( ExternalLinkToRemove.objects.count(), 0 )

        self.assertEqual( len( mail.outbox ), 1 )

        print mail.outbox[0].body

        self.assertTrue( self.film.get_absolute_url() in mail.outbox[0].body )
