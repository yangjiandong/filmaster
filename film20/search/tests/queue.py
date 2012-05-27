#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

from unittest import skipIf
from datetime import datetime

from film20.utils.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command

from film20.config.urls import urls
from film20.core.models import Film
from film20.blog.models import Post
from film20.search.models import QueuedItem

from film20.search.tests.base import SearchTestCase, is_supported

@skipIf( not is_supported(), "search tests only runs when solr is supported" )
class ModelsTestCase( SearchTestCase ):

    def setUp( self ):
        super( ModelsTestCase, self ).setUp()
        self.tearDown()
        self.daemon.start()
        # ...
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )
        self.u1.save()

    def tearDown( self ):
        self.daemon.stop()
        # ...
        User.objects.all().delete()
        Film.objects.all().delete()
        QueuedItem.objects.all().delete()

    def testQueuedItem( self ):
        self.assertEqual( QueuedItem.objects.count(), 1 )
        self.assertTrue( isinstance( QueuedItem.objects.all()[0].content_object, User ) )
 
        f = Film( type=1, permalink='przypadek', imdb_code=111, status=1, version=1, \
                 release_year=1999, title='Przypadek' )
        f.save()
        
        self.assertEqual( QueuedItem.objects.count(), 3 )
        self.assertTrue( isinstance( QueuedItem.objects.all()[1].content_object, Film ) )
        
        modified_at = QueuedItem.objects.all()[1].modified_at

        f.title = 'Przypadek - test'
        f.save()

        self.assertEqual( QueuedItem.objects.count(), 3 )
        self.assertTrue( QueuedItem.objects.all()[1].modified_at > modified_at )

        f.delete()

        self.assertEqual( QueuedItem.objects.all()[1].action_type, QueuedItem.ACTION_REMOVED )
        self.assertEqual( QueuedItem.objects.count(), 3 )
    
    def testBlogPostIndex( self ):
        self.client.login( username='user', password='user' ) 
        data = {
            'title' : "Lorem ipsum",
            'body' : "Lorem ipsum! Lorem ipsum! Lorem ipsum!",
            'save' : True,
        }

        response = self.client.post( "/%s/" % urls["NEW_ARTICLE"], data )

        self.failUnlessEqual( Post.objects.count(), 1 )
        self.assertEqual( QueuedItem.objects.count(), 2 )
        self.assertEqual( QueuedItem.objects.all()[1].action_type, QueuedItem.ACTION_REMOVED )

        post = Post.objects.all()[0]
        post.status = Post.PUBLIC_STATUS
        post.save()

        self.assertEqual( QueuedItem.objects.count(), 2 )
        self.assertEqual( QueuedItem.objects.all()[1].action_type, QueuedItem.ACTION_UPDATED )

        call_command( 'update_index_queue' )
        
        self.assertEqual( QueuedItem.objects.count(), 0 )

    def testQueueCommand( self ):
        f = Film( type=1, permalink='przypadek', imdb_code=111, status=1, version=1, \
                 release_year=1999, title='Przypadek' )
        f.save()
        f.delete()
    
        self.assertEqual( QueuedItem.objects.count(), 3 )

        call_command( 'update_index_queue' )
        
        self.assertEqual( QueuedItem.objects.count(), 1 )

