from django.core import mail
from django.test import Client
from django.contrib.auth.models import User

from film20.core.models import Film, Object, ObjectLocalized, FilmLocalized
from film20.moderation.urls import urlpatterns
from film20.moderation.registry import registry
from film20.moderation.tests.base import BaseTest
from film20.tagging.models import Tag, TagAlias, TaggedItem

class TaggingToolsTestCase( BaseTest ):
    
    def setUp( self ):
        super( TaggingToolsTestCase, self ).setUp()
        # ..
        self.admin = User.objects.create_user( "admin", "admin@admin.com", "admin" )
        self.admin.is_superuser = True
        self.admin.save()

        self.client = Client( follow=True )

        self.rename_tag = registry.get_by_name( 'rename-tag' )
        self.alias_tag = registry.get_by_name( 'alias-tag' )

        self.film1 = Film()
        self.film1.title = "Battlefield Earth II"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "battlefirld-earth-ii"
        self.film1.release_year = 2010
        self.film1.production_country_list = "USA"
        self.film1.save()
        self.film1.save_tags( "komedia, kosmos, test" )

        self.film2 = Film()
        self.film2.title = "Battlefield Earth III"
        self.film2.type = Object.TYPE_FILM
        self.film2.permalink = "battlefirld-earth-iii"
        self.film2.release_year = 2011
        self.film2.production_country_list = "USA"
        self.film2.save()
        self.film2.save_tags( "komedia, kosmos, test" )

        self.film3 = Film()
        self.film3.title = "Battlefield Earth IV"
        self.film3.type = Object.TYPE_FILM
        self.film3.permalink = "battlefirld-earth-iv"
        self.film3.release_year = 2012
        self.film3.production_country_list = "Italy"
        self.film3.save()
        self.film3.save_tags( "komedia romantyczna, kosmos, test" )

        self.tag1 = Tag.objects.create( name='ciekawy' )

    def tearDown( self ):
        super( TaggingToolsTestCase, self ).tearDown()
        
        mail.outbox = []

        Tag.objects.all().delete()
        Film.objects.all().delete()

    def testRenamingWithNoAssignedObjects( self ):

        self.client.login( username='admin', password='admin' )
        response = self.client.get( self.rename_tag.get_absolute_url() )
        self.assertEqual( response.status_code, 200 )

        self.assertEqual( Tag.objects.filter( name='komedia' ).count(), 1 )
        self.assertEqual( Tag.objects.filter( name=self.tag1.name ).count(), 1 )
        self.assertEqual( TaggedItem.objects.filter( tag__name='komedia' ).count(), 2 )
        self.assertEqual( TaggedItem.objects.filter( tag__name=self.tag1.name ).count(), 0 )

        data = {
            'tagA': self.tag1.name,
            'tagB': 'komedia',
            'confirm': 'true'
        }

        response = self.client.post( self.rename_tag.get_absolute_url(), data )
        self.assertEqual( response.status_code, 302 )

        self.assertEqual( len( mail.outbox ), 1 )
        print mail.outbox[0].body

        self.assertEqual( Tag.objects.filter( name='komedia' ).count(), 1 )
        self.assertEqual( Tag.objects.filter( name=self.tag1.name ).count(), 0 )
        self.assertEqual( TaggedItem.objects.filter( tag__name='komedia' ).count(), 2 )
        self.assertEqual( TaggedItem.objects.filter( tag__name=self.tag1.name ).count(), 0 )

    def testRenamingWithAssignedObjects( self ):
        
        self.client.login( username='admin', password='admin' )
        response = self.client.get( self.rename_tag.get_absolute_url() )
        self.assertEqual( response.status_code, 200 )

        self.assertEqual( Tag.objects.filter( name='komedia' ).count(), 1 )
        self.assertEqual( Tag.objects.filter( name='komedia romantyczna' ).count(), 1 )
        self.assertEqual( TaggedItem.objects.filter( tag__name='komedia' ).count(), 2 )
        self.assertEqual( TaggedItem.objects.filter( tag__name='komedia romantyczna' ).count(), 1 )

        data = {
            'tagA': 'komedia romantyczna',
            'tagB': 'komedia',
            'confirm': 'true'
        }

        response = self.client.post( self.rename_tag.get_absolute_url(), data )
        self.assertEqual( response.status_code, 302 )

        self.assertEqual( len( mail.outbox ), 1 )
        print mail.outbox[0].body

        self.assertEqual( Tag.objects.filter( name='komedia' ).count(), 1 )
        self.assertEqual( Tag.objects.filter( name='komedia romantyczna' ).count(), 0 )
        self.assertEqual( TaggedItem.objects.filter( tag__name='komedia' ).count(), 3 )
        self.assertEqual( TaggedItem.objects.filter( tag__name='komedia romantyczna' ).count(), 0 )

    def testAliasingTagsWithNoAssignedObjects( self ):

        self.client.login( username='admin', password='admin' )
        response = self.client.get( self.alias_tag.get_absolute_url() )
        self.assertEqual( response.status_code, 200 )

        self.assertEqual( TagAlias.objects.count(), 0 )

        tag = Tag.objects.create( name='science-fiction' )

        data = {
            'tag': tag.name,
            'aliases': 'sci-fi, science fiction, scifi',
        }

        response = self.client.post( self.alias_tag.get_absolute_url(), data )
        self.assertEqual( response.status_code, 302 )

        self.assertEqual( TagAlias.objects.count(), 3 )

    def testAliasingTagsWithAssignedObjects( self ):

        self.client.login( username='admin', password='admin' )
        response = self.client.get( self.alias_tag.get_absolute_url() )
        self.assertEqual( response.status_code, 200 )

        self.assertEqual( TagAlias.objects.count(), 0 )

        data = {
            'tag': 'komedia',
            'aliases': 'sit-com, comedy, komedia romantyczna',
        }

        response = self.client.post( self.alias_tag.get_absolute_url(), data )
        self.assertEqual( response.status_code, 200 )

        self.assertEqual( TagAlias.objects.count(), 0 )

    def testAssigningAliasTag( self ):
        
        self.testAliasingTagsWithNoAssignedObjects()
        self.assertEqual( TagAlias.objects.count(), 3 )
        
        self.assertEqual( self.film1.get_tags(), "komedia, kosmos, test" )

        self.film1.save_tags( "komedia, kosmos, test, scifi" )

        self.assertEqual( self.film1.get_tags(), "komedia, kosmos, science-fiction, test" )
