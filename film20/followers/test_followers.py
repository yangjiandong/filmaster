from film20.utils.test import TestCase
from django.core import mail

from film20.followers.models import *

class FollowersTestCase(TestCase):

    u1 = None
    u2 = None
    u3 = None
    u4 = None

    def setUp(self):
        Followers.objects.all().delete()
        User.objects.all().delete()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()
        self.u2 = User(username='adz', email='b.orysmusielak@gmail.com')
        self.u2.save()
        self.u3 = User(username='turin', email='borysm.usielak@gmail.com')
        self.u3.save()
        self.u4 = User(username='olamus', email='borysmu.sielak@gmail.com')
        self.u4.save()

    def tearDown(self):
        Followers.objects.all().delete()
        User.objects.all().delete()

    def test_follow(self):
        """
            Testing adding to follow list. u1 wants to follow u2,u3,u4
            After it following() should return list with 3 users for u1
            For u2 followers() should return 1
        """
        self.u1.followers.follow(self.u2)
        self.u1.followers.follow(self.u3)
        self.u1.followers.follow(self.u4)

        self.assertEquals(len(self.u1.followers.following()), 3)
        self.assertEquals(len(self.u2.followers.followers()), 1)

    def test_followers(self):
        """
           Testing followers. u2, u3, u3 want to follow u1.
           After it followers() should return list with 3 users for u1
           For u2 following() should return 1
        """
        self.u2.followers.follow(self.u1)
        self.u3.followers.follow(self.u1)
        self.u4.followers.follow(self.u1)

        self.assertEquals(len(self.u1.followers.followers()), 3)
        self.assertEquals(len(self.u2.followers.following()), 1)

    def test_block(self):
        """
           Testing blocking. u1 wants to block u2, u3, u4.
           After it blocking for u1 should return list with 3 users,
           and blockers for u2 should return 1
        """
        self.u1.followers.block(self.u2)
        self.u1.followers.block(self.u3)
        self.u1.followers.block(self.u4)

        self.assertEquals(len(self.u1.followers.blocking()), 3)
        self.assertEquals(len(self.u2.followers.blockers()), 1)

    def test_blockers(self):
        """
           Testing blockers. u2, u3, u4 want to block u1.
           After it blockers() should return list with 3 users for u1.
           blocking() for u1 should return 1
        """
        self.u2.followers.block(self.u1)
        self.u3.followers.block(self.u1)
        self.u4.followers.block(self.u1)

        self.assertEquals(len(self.u1.followers.blockers()), 3)
        self.assertEquals(len(self.u2.followers.blocking()), 1)

    def test_remove(self):
        """
           Testing remove. u1 wants to block u2, then he decides to follow u2
           u3 follow u4 but he don't want to do it
        """
        self.u1.followers.block(self.u2)
        self.assertEquals(len(self.u1.followers.blocking()), 1)

        self.u1.followers.follow(self.u2)
        self.assertEquals(len(self.u1.followers.blocking()), 1)

        self.u3.followers.follow(self.u4)
        self.assertEquals(len(self.u3.followers.following()), 1)

        self.u3.followers.remove(self.u4)
        self.assertEquals(len(self.u3.followers.following()), 0)
        a = self.u3.from_users.get(from_user=self.u3)
        self.assertEquals(a.status, Followers.UNKNOWN)

    def test_friends(self):
        """
           u1 and u2 follow each other they are friends,
           friends() for u1 should return 1 becasue he has only one friend
        """
        self.u1.followers.follow(self.u2)
        self.u2.followers.follow(self.u1)

        self.assertEquals(len(self.u1.followers.friends()), 1)

    def test_relation(self):
        """
            u1 follows u2 test should return relation
            u1 don't follow u3 test should return false
        """
        self.u1.followers.follow(self.u2)
        relation = self.u1.followers.get_relation(self.u2)
        self.assertEquals(relation is not False, True)

        relation = self.u1.followers.get_relation(self.u3)
        self.assertEquals(relation, False)

    def test_notification(self):
        """
            test sending notifications
        """
        self.u1.followers.follow(self.u2)
        self.assertEqual(len(mail.outbox), 1)

    def test_follow_on_create( self ):
        """
            test following filmaster on user create
        """
        filmaster = User.objects.create_user( 'blog', 'filmaster@filmaster.com', 'blog')
        user = User.objects.create_user( 'user', 'user@user.com', 'user' )
        
        self.assertEquals( len( user.followers.following() ), 1 )
        self.assertEquals( len( user.followers.followers() ), 0 )
        self.assertEquals( len( filmaster.followers.following() ), 0 )
        self.assertEquals( len( filmaster.followers.followers() ), 1 )

        self.assertEqual( len( mail.outbox ), 0 )


    def test_follow_command( self ):
        """
            test following filmaster command
        """
        from django.core.management import call_command
       
        filmaster = User.objects.create_user( 'blog', 'filmaster@filmaster.com', 'blog')

        self.assertEquals( len( filmaster.followers.following() ), 0 )
        
        self.assertEquals( len( self.u1.followers.following() ), 0 )
        self.assertEquals( len( self.u2.followers.following() ), 0 )
        self.assertEquals( len( self.u3.followers.following() ), 0 )
        self.assertEquals( len( self.u4.followers.following() ), 0 )

        call_command( 'add_filmaster_to_followed' )

        self.assertEquals( len( filmaster.followers.followers() ), 4 )
        
        self.assertEquals( len( self.u1.followers.following() ), 1 )
        self.assertEquals( len( self.u2.followers.following() ), 1 )
        self.assertEquals( len( self.u3.followers.following() ), 1 )
        self.assertEquals( len( self.u4.followers.following() ), 1 )

        self.assertEqual( len( mail.outbox ), 0 )

