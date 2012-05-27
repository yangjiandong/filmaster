from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType

from film20.utils.test import TestCase
from film20.tagging.models import Tag, TaggedItem
from film20.core.models import Film, Object, FilmLocalized

class CommandsTestCase( TestCase ):

    def setUp( self ):

        # set up films
        self.film1 = Film()
        self.film1.title = "Battlefield Earth II"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "battlefirld-earth-ii"
        self.film1.release_year = 2010
        self.film1.production_country_list = "USA"
        self.film1.save()
        self.film1.save_tags( "sciencie-fiction komedia test1 test2", LANG="pl", saved_by=2)

        self.film2 = Film()
        self.film2.title = "Battlefield Earth III"
        self.film2.type = Object.TYPE_FILM
        self.film2.permalink = "battlefirld-earth-iii"
        self.film2.release_year = 2011
        self.film2.production_country_list = "USA"
        self.film2.save()
        self.film2.save_tags("sciencie-fiction komedia test1", LANG="pl", saved_by=2)

        self.film3 = Film()
        self.film3.title = "Battlefield Earth IV"
        self.film3.type = Object.TYPE_FILM
        self.film3.permalink = "battlefirld-earth-iv"
        self.film3.release_year = 2012
        self.film3.production_country_list = "Italy"
        self.film3.save()
        self.film3.save_tags("sciencie-fiction komedia test3 test5", LANG="pl", saved_by=2)

        self.film4 = Film()
        self.film4.title = "Battlefield Earth V"
        self.film4.type = Object.TYPE_FILM
        self.film4.permalink = "battlefirld-earth-v"
        self.film4.release_year = 2013
        self.film4.production_country_list = "UK"
        self.film4.save()
        self.film4.save_tags("sciencie-fiction komedia test5", LANG="en", saved_by=2)
        self.film4.save_tags("sciencie-fiction komedia", LANG="en", saved_by=2)

        self.film5 = Film()
        self.film5.title = "Battlefield Earth VI"
        self.film5.type = Object.TYPE_FILM
        self.film5.permalink = "battlefirld-earth-vi"
        self.film5.release_year = 2013
        self.film5.production_country_list = "UK"
        self.film5.save()
        self.film5.save_tags("sciencie-fiction comedy", LANG="en", saved_by=2)

    def tearDown( self ):
        Tag.all_objects.all().delete()
        Film.objects.all().delete()

    def test_remove_unused_tags( self ):
        self.assertEqual( Tag.all_objects.filter( LANG='pl' ).count(), 6 )
        self.assertEqual( Tag.all_objects.filter( LANG='en' ).count(), 4 )

        call_command( 'remove_unused_tags' )

        self.assertEqual( Tag.all_objects.filter( LANG='pl' ).count(), 6 )
        self.assertEqual( Tag.all_objects.filter( LANG='en' ).count(), 3 )

    def test_duplicate_localized_tags( self ):
        obj, created = FilmLocalized.objects.get_or_create( parent=self.film1, film=self.film1, LANG='pl' )
        ctype = ContentType.objects.get_for_model( obj )
        tag, created = Tag.all_objects.get_or_create( name='scifi', LANG='en' )
        
        TaggedItem._default_manager.get_or_create( tag=tag, content_type=ctype, object_id=obj.pk )
        
        self.assertEqual( Tag.all_objects.filter( LANG='pl' ).count(), 6 )
        self.assertEqual( Tag.all_objects.filter( LANG='en' ).count(), 5 )
        self.assertEqual( TaggedItem.all_objects.count(), 16 )

        call_command( 'duplicate_localized_tags' )
        
        self.assertEqual( Tag.all_objects.filter( LANG='pl' ).count(), 7 )
        self.assertEqual( Tag.all_objects.filter( LANG='en' ).count(), 3 )
        self.assertEqual( TaggedItem.all_objects.count(), 16 )

        tagged_item = TaggedItem._default_manager.get( content_type=ctype, object_id=obj.pk )
        self.assertEqual( tagged_item.tag.name, 'scifi' )
        self.assertEqual( tagged_item.tag.LANG, 'pl' )
