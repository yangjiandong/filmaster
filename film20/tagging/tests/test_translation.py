from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType

from film20.utils.test import TestCase
from film20.core.models import Film, Object, ObjectLocalized
from film20.tagging.models import Tag, TaggedItem, TagTranslation

def get_tags( flm ):
    tags = {}
    for loc in ObjectLocalized.objects.filter( parent=flm.id ):
        for tag in Tag.objects.get_for_object( loc ):
            if not tags.has_key( loc.LANG ):
                tags[loc.LANG] = []
            tags[loc.LANG].append( tag.name )
    return tags

def get_tags_as_string( flm, LANG=None ):
    tags = get_tags( flm )
    if not tags.has_key( LANG ):
        return ''
    return ','.join( tags[LANG] )

class TagTranslationTestCase( TestCase ):

    def setUp( self ):

        # set up films
        self.film1 = Film()
        self.film1.title = "Film 1"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "film-1"
        self.film1.release_year = 2010
        self.film1.production_country_list = "USA"
        self.film1.save()
        self.film1.save_tags( "dramat komedia ", LANG="pl", saved_by=2 )
        self.film1.save_tags( "drama comedy wizards ", LANG="en", saved_by=2 )


    def tearDown( self ):
        Tag.all_objects.all().delete()
        Film.objects.all().delete()

    def test_translation_1( self ):

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'dramat,komedia' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'comedy,drama,wizards' )

        TagTranslation.create_translation( 'drama', 'dramat', 'en', 'pl' )
        TagTranslation.create_translation( 'comedy', 'komedia', 'en', 'pl' )
        TagTranslation.create_translation( 'vampires', 'wampiry', 'en', 'pl' )

        self.film1.save_tags( "dramat komedia wampiry", LANG="pl", saved_by=2 )

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'dramat,komedia,wampiry' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'comedy,drama,vampires,wizards' )

    def test_translation_2( self ):

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'dramat,komedia' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'comedy,drama,wizards' )

        TagTranslation.create_translation( 'drama', 'dramat', 'en', 'pl' )
        TagTranslation.create_translation( 'comedy', 'komedia', 'en', 'pl' )

        self.film1.save_tags( "dramat komedia wampiry", LANG="pl", saved_by=2 )

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'dramat,komedia,wampiry' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'comedy,drama,wizards' )

    def test_translation_3( self ):

        TagTranslation.create_translation( 'drama', 'dramat', 'en', 'pl' )
        TagTranslation.create_translation( 'comedy', 'komedia', 'en', 'pl' )

        self.film1.save_tags( "test test1", LANG="en", saved_by=2 )
        self.film1.save_tags( "dramat komedia wampiry", LANG="pl", saved_by=2 )

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'dramat,komedia,wampiry' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'comedy,drama,test,test1' )

    def test_translation_4( self ):

        self.film1.save_tags( "test test1", LANG="en", saved_by=2 )
        self.film1.save_tags( "dramat komedia wampiry", LANG="pl", saved_by=2 )

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'dramat,komedia,wampiry' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'test,test1' )

    def test_command( self ):
        from django.db import connection, transaction
        from django.core.management import call_command
        from django.contrib.contenttypes.models import ContentType
        
        cursor = connection.cursor()    

        query = """
            INSERT INTO tagging_taggeditem ( tag_id, content_type_id, object_id ) VALUES( %d, %d, %d )
        """        

        self.film1.save_tags( "", LANG="pl", saved_by=2 )
        self.film1.save_tags( "", LANG="en", saved_by=2 )

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), '' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), '' )
        
        content_type_id = ContentType.objects.get_for_model( ObjectLocalized ).pk
        en_object = ObjectLocalized.objects.get( parent=self.film1.pk, LANG="en" )
        pl_object = ObjectLocalized.objects.get( parent=self.film1.pk, LANG="pl" )

        for name in "en1", "en2":
            tag, created = Tag.all_objects.get_or_create( LANG="en", name=name ) 
            cursor.execute( query % ( tag.id, content_type_id, en_object.pk ) )

        for name in "polski", "polski2", "polski3":
            tag, created = Tag.all_objects.get_or_create( LANG="pl", name=name ) 
            cursor.execute( query % ( tag.id, content_type_id, pl_object.pk ) )

        transaction.commit()

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'polski,polski2,polski3' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'en1,en2' )

        TagTranslation.create_translation( 'en1', 'pl1', 'en', 'pl' )
        TagTranslation.create_translation( 'en2', 'pl2', 'en', 'pl' )

        call_command( 'translate_tags' )

        self.assertEqual( get_tags_as_string( self.film1, 'pl' ), 'pl1,pl2,polski,polski2,polski3' )
        self.assertEqual( get_tags_as_string( self.film1, 'en' ), 'en1,en2' )


