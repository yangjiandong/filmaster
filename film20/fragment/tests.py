from django.template import Context, Template

from film20.utils.test import TestCase
from film20.fragment.models import Fragment

class FragmentTest( TestCase ):
    def setUp( self ):
        self.f1 = Fragment.objects.create( name="Test 1", key="test", body="Test 1" )
        self.f2 = Fragment.objects.create( name="Test 2", key="test", body="Test 2" )
        
        self.f3 = Fragment.objects.create( name="Test 3", key="test-single", body="Test 3" )

    def cleanUp( self ):
        Fragment.objects.all().delete()

    def testBase( self ):
        self.assertEqual( Fragment.objects.count(), 3 )

    def testSingleFragment( self ):

        template = Template( '{% load fragments %}{% fragment test-single %}' )
        context = Context( {} )
        
        self.assertEqual( template.render( context ), 'Test 3' )
        self.assertEqual( template.render( context ), 'Test 3' )

    def testFragmentDoesNotExists( self ):

        template = Template( '{% load fragments %}{% fragment missing-fragment %}' )
        context = Context( {} )
        
        self.assertEqual( template.render( context ), '' )
        self.assertEqual( template.render( context ), '' )


    def testRotation( self ):

        template = Template( '{% load fragments %}{% fragment test %}' )
        context = Context( {} )
        
        self.assertEqual( template.render( context ), 'Test 2' )
        self.assertEqual( template.render( context ), 'Test 1' )
        self.assertEqual( template.render( context ), 'Test 2' )
        self.assertEqual( template.render( context ), 'Test 1' )

