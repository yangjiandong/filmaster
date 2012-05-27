# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import unittest
from django.conf import settings
from film20.utils.test import TestCase, integration_test
from film20.import_films.imdb_fetcher import run
from film20.core.models import Object, Film, Person, Character
from film20.import_films.models import FilmToImport, ImportedFilm
from film20.import_films.management.commands.fix_imported_persons import unescape, compare

class PersonFixerTestCase( TestCase ):

    def setUp( self ):
        self.user= User.objects.create_user( 'user', 'user@user.com', 'user' )

    @integration_test
    def test_persons( self ):

        fti1 = FilmToImport( user=self.user, title='Nybyggarna',
                imdb_url='http://www.imdb.com/title/tt0069035/', imdb_id='0069035', status=FilmToImport.ACCEPTED )
        fti1.save()

        fti2 = FilmToImport( user=self.user, title='Utvandrarna',
                imdb_url='http://www.imdb.com/title/tt0067919/', imdb_id='0067919', status=FilmToImport.ACCEPTED )
        fti2.save()

        fti3 = FilmToImport( user=self.user, title='Sandade Sandadi',
                imdb_url='http://www.imdb.com/title/tt0338408/', imdb_id='0338408', status=FilmToImport.ACCEPTED )
        fti3.save()

        fti4 = FilmToImport( user = self.user, title = 'Journey to shiloh',
                imdb_url = 'http://www.imdb.com/title/tt0063161/', imdb_id = '0063161', status = FilmToImport.ACCEPTED )
        fti4.save()

        fti5 = FilmToImport( user = self.user, title = 'Guys choice Awards 2011',
                imdb_url = 'http://www.imdb.com/title/tt2023505/', imdb_id = '2023505', status = FilmToImport.ACCEPTED )
        fti5.save()

        self.assertTrue( compare( "Pen&#xE9;lope Cruz", "Penélope Cruz", 2 ) )
 
        fti6 = FilmToImport( user=self.user, title='Volver',
                imdb_url='http://www.imdb.com/title/tt0441909/', imdb_id='0441909', status=FilmToImport.ACCEPTED )
        fti6.save()

        fti7 = FilmToImport( user=self.user, title='Gothika',
                imdb_url='http://www.imdb.com/title/tt0348836/', imdb_id='0348836', status=FilmToImport.ACCEPTED )
        fti7.save()
        
        run( False, False, False, False, False, True, "http" )

        self.assertEqual( Film.objects.count(), 7 )
        self.assertEqual( Person.objects.filter( name='Harrison', surname='Ford', imdb_code='0000148', verified_imdb_code=True ).count(), 1 )
        self.assertEqual( Person.objects.filter( name='Yvonne', surname='Oppstedt', imdb_code='0649235', verified_imdb_code=True ).count(), 1 )
        self.assertEqual( Person.objects.filter( name='Sonali', surname='Joshi', imdb_code='1359890', verified_imdb_code=True ).count(), 1 )
        self.assertEqual( Film.objects.filter( character__person__imdb_code='0649235' ).distinct().count(), 2 )
        self.assertEqual( Film.objects.filter( character__person__imdb_code='1359890' ).distinct().count(), 1 )

        # 1. two persons merged
        f1 = Film.objects.get( imdb_code='0338408' )
    
        yvonne = Person.objects.get( imdb_code='0649235' )
        sonali = Person.objects.get( imdb_code='1359890' )

        for ch in Character.objects.filter( person=sonali, film=f1 ):
            ch.person = yvonne
            ch.save()

        self.assertEqual( Film.objects.filter( character__person=yvonne ).distinct().count(), 3 )
        self.assertEqual( Film.objects.filter( character__person=sonali ).distinct().count(), 0 )

        sonali.delete()

        yvonne.imdb_code = '1359890'
        yvonne.verified_imdb_code = False
        yvonne.import_comment = 'imdb name: Sonali Joshi'
        yvonne.save()
        
        # 2. one person with two movies
        f2 = Film.objects.get( imdb_code='2023505' )

        harrison = Person.objects.get( imdb_code='0000148' )

        bad_harrison = Person()
        bad_harrison.name = "Harrison"
        bad_harrison.surname = "Ford"
        bad_harrison.permalink = "harrison-ford-1"
        bad_harrison.type = Person.TYPE_PERSON
        bad_harrison.save()

        for ch in Character.objects.filter( person=harrison, film=f2 ):
            ch.person = bad_harrison
            ch.save()

        harrison.verified_imdb_code = False
        harrison.imdb_code = '111111'
        harrison.save()

        bad_harrison.verified_imdb_code = True
        bad_harrison.imdb_code = '0000148'
        bad_harrison.save()

        self.assertEqual( Film.objects.filter( character__person=harrison ).distinct().count(), 1 )
        self.assertEqual( Film.objects.filter( character__person=bad_harrison ).distinct().count(), 1 )
        self.assertEqual( Person.objects.filter( verified_imdb_code=False ).count(), 2 )
 
        # 3. short imdb code duplicated
        self.assertEqual( Person.objects.filter( imdb_code='0880521', name='Liv', surname='Ullmann' ).count(), 1 )

        liv = Person.objects.get( imdb_code='0880521' )
        liv.permalink = 'liv-ullmann-1'
        liv.save()

        short_liv = Person()
        short_liv.imdb_code = '880521'
        short_liv.name = 'Liv' 
        short_liv.surname = 'Ullmann'
        short_liv.permalink = 'liv-ullmann'
        short_liv.type = Person.TYPE_PERSON
        short_liv.save()
 
        # 4. not verified imdb_code
        self.assertEqual( Person.objects.filter( imdb_code='0005493', name='Justin', surname='Timberlake', verified_imdb_code=True ).count(), 1 )
        
        justin = Person.objects.get( imdb_code='0005493' )
        justin.verified_imdb_code = False
        justin.imdb_code = None
        justin.save()

        self.assertEqual( Person.objects.filter( imdb_code='0873296', name='Jan', surname='Troell', verified_imdb_code=True ).count(), 1 )
        
        jan = Person.objects.get( imdb_code='0873296' )
        jan.verified_imdb_code = False
        jan.save()

        # 5. html entities in name
        self.assertEqual( Person.objects.filter( name='Penélope', surname='Cruz', imdb_code='0004851', verified_imdb_code=True ).count(), 1 )
        
        penelope = Person.objects.get( imdb_code='0004851' )
        gothika = Film.objects.get( imdb_code='0348836' )

        penelope.verified_imdb_code = False
        penelope.imdb_code = '4851'
        penelope.save()

        bad_penelope = Person()
        bad_penelope.name = "Pen&#xE9;lope"
        bad_penelope.surname = "Cruz"
        bad_penelope.imdb_code = '0004851'
        bad_penelope.permalink = "penxe9lope-cruz"
        bad_penelope.type = Person.TYPE_PERSON
        bad_penelope.save()

        for ch in Character.objects.filter( person=penelope, film=gothika ):
            ch.person = bad_penelope
            ch.save()

        call_command( 'fix_imported_persons' )

        #for p in Person.objects.all():
        #    print p.verified_imdb_code, p, p.imdb_code, p.import_comment

        self.assertEqual( Person.objects.filter( verified_imdb_code=False ).count(), 1 )
        self.assertEqual( Film.objects.filter( character__person=harrison ).distinct().count(), 2 )
        self.assertEqual( Person.objects.get( pk=yvonne.pk ).import_comment, 'imdb name: Sonali Joshi, not matched movies: 0338408' )
        self.assertEqual( Person.objects.filter( imdb_code='880521' ).count(), 0 )
        self.assertEqual( Person.objects.filter( imdb_code='0880521', name='Liv', surname='Ullmann' ).count(), 1 )
        
        justin = Person.objects.get( pk=justin.pk )
        self.assertEqual( justin.imdb_code, '0005493' )
        self.assertTrue( justin.verified_imdb_code )

        jan = Person.objects.get( pk=jan.pk )
        self.assertEqual( jan.imdb_code, '0873296' )
        self.assertTrue( jan.verified_imdb_code )
        
        self.assertEqual( Person.objects.filter( name='Penélope', surname='Cruz', imdb_code='0004851', verified_imdb_code=True ).count(), 1 )
        acted = Film.objects.filter( character__person=penelope ).distinct()
        self.assertTrue( len( acted ), 2 )
 




