# Python

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse, clear_url_caches
from django.conf import settings

# Project
from film20.utils.test import TestCase
from film20.core.models import Film, Object
from film20.blog.models import Post
from film20.config.urls import *
from film20.useractivity.models import UserActivity

class PostTestCase(TestCase):

    u1 = None
    film = None

    def setUp(self):
        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save(saved_by=2)

    def tearDown(self):
        User.objects.all().delete()
        Post.objects.all().delete()
        UserActivity.objects.all().delete()
        Film.objects.all().delete()

    def test_edit_existing_post(self):
        """
            Case where user is trying to edit existing post 
        """
        self.client.login(username=self.u1.username, password='secret')

        # set up post
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()
        post.related_film.add(self.film)
        # this method will call save_activity method and in this case create new activity
        post.save()
        
        first_publish = post.publish
        # make sure published date is set
        self.failIf(first_publish is None)

        post.title = "Lorem ipsum! Lorem ipsum! Lorem ipsum!"
        post.save()
        
        # published date should not change after saving again
        self.failUnlessEqual(first_publish, post.publish)

        # make sure related activity also gets updated
        from film20.useractivity.models import UserActivity
        activity = UserActivity.objects.get(activity_type = UserActivity.TYPE_POST, post = post, user = post.user)

        post = Post.objects.get(permalink="lorem-ipsum")
        self.failUnlessEqual(post.title, "Lorem ipsum! Lorem ipsum! Lorem ipsum!")
        self.failUnlessEqual(activity.slug, "/" + urls['SHOW_PROFILE'] + '/' + self.u1.username + '/' + urls['ARTICLE'] + "/lorem-ipsum/")


        # now revert ro draft and then republish
        post.status = Object.DRAFT_STATUS
        post.save()
        post.status = Object.PUBLIC_STATUS
        post.save()

        # published date should not change after republishing an article published before
        self.failUnlessEqual(first_publish, post.publish)

    def test_edit_deleted_post(self):
        """
            Test case where user is trying to edit not existing post
            for example from old link
        """
        self.client.login(username=self.u1.username, password='secret')

        # accesing by id
        # 404 code should be sent
        get_form_url = "/"+urls["EDIT_ARTICLE"]+"/623289/"

        response = self.client.get(
                        get_form_url,
                   )
        self.failUnlessEqual(response.status_code, 404)

    def test_all_for_user(self):
        """
           Test all_for_user manager
        """
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Post.PUBLIC_STATUS
        post.type = Post.TYPE_POST
        post.save()

        post1 = Post()
        post1.title = "Lorem ipsum2"
        post1.permalink = "lorem-ipsum"
        post1.body = "siala lala tralala"
        post1.user = self.u1
        post1.status = Post.DRAFT_STATUS
        post1.type = Post.TYPE_POST
        post1.save()

        self.assertEqual(Post.objects.all_for_user(self.u1).count(), 2)

    def test_public_for_user(self):
        """
            Test public_for_user manager
        """
        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Post.PUBLIC_STATUS
        post.type = Post.TYPE_POST
        post.save()

        post1 = Post()
        post1.title = "Lorem ipsum2"
        post1.permalink = "lorem-ipsum"
        post1.body = "siala lala tralala"
        post1.user = self.u1
        post1.status = Post.DRAFT_STATUS
        post1.type = Post.TYPE_POST
        post1.save()

        self.assertEqual(Post.objects.public_for_user(self.u1).count(), 1)

    def test_empty_page_response(self):
        """
        test response for empty page
        """
        response = self.client.get(reverse('movies'))
        self.failUnlessEqual(response.status_code, 200)
        self.assertEqual(len(response.context['recent_reviews']), 0)
        self.assertEqual(len(response.context['featured_film']), 0)

    def test_cache_recent_reviews(self):
        """
        test cache invalidate for recent reviews
        """
        posts = Post.objects.recent_reviews()
        self.assertEqual(len(posts), 0)

        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Post.PUBLIC_STATUS
        post.type = Post.TYPE_POST
        post.is_published = True
        post.save()

        posts = Post.objects.recent_reviews()
        self.assertEqual(posts.count(), 1)

        post1 = Post()
        post1.title = "Lorem ipsum2"
        post1.permalink = "lorem-ipsum2"
        post1.body = "siala lala tralala"
        post1.user = self.u1
        post1.status = Post.PUBLIC_STATUS
        post1.type = Post.TYPE_POST
        post1.is_published = True
        post1.save()

        posts = Post.objects.recent_reviews()
        featured = Post.objects.featured_review()
        self.assertEqual(posts.count(),2)
        self.assertEqual(featured, None)

        post2 = Post()
        post2.title = "third post"
        post2.permalink = "third-post"
        post2.body = "siala lala tralala"
        post2.user = self.u1
        post2.status = Post.PUBLIC_STATUS
        post2.type = Post.TYPE_POST
        post2.is_published = True
        post2.save()

        posts = Post.objects.recent_reviews()
        featured = Post.objects.featured_review()
        self.assertEqual(posts.count(),3)
        self.assertEqual(featured, None)

        # change featured post status and check if cache is invalidated
        post2 = Post.objects.get(title__iexact='third post')
        post2.status = Post.DRAFT_STATUS
        post2.save()

        posts = Post.objects.recent_reviews()
        featured = Post.objects.featured_review()
        self.assertEqual(posts.count(),2)
        self.assertEqual(featured, None)

        # republished post
        post2 = Post.objects.get(title__iexact='third post')
        post2.status = Post.PUBLIC_STATUS
        post2.save()

        posts = Post.objects.recent_reviews()
        featured = Post.objects.featured_review()
        self.assertEqual(posts.count(),3)
        self.assertEqual(featured, None)

    def test_cache_featured_review(self):
        """
        test cache invalidate for featured review
        """
        post = Post.objects.featured_review()
        self.assertEqual(post, None)

        post = Post()
        post.title = "first post"
        post.permalink = "first-post"
        post.body = "post first post"
        post.user = self.u1
        post.status = Post.PUBLIC_STATUS
        post.type = Post.TYPE_POST
        post.featured_note = True
        post.save()

        post = Post.objects.featured_review()
        self.assertEqual(post.permalink, u'first-post')

        post1 = Post()
        post1.title = "second post"
        post1.permalink = "second-post"
        post1.body = "post second post"
        post1.user = self.u1
        post1.status = Post.PUBLIC_STATUS
        post1.type = Post.TYPE_POST
        post1.featured_note = True
        post1.save()

        post = Post.objects.featured_review()
        self.assertEqual(post.permalink, u'second-post')

        post2 = Post()
        post2.title = "third post"
        post2.permalink = "third-post"
        post2.body = "post third post"
        post2.user = self.u1
        post2.status = Post.PUBLIC_STATUS
        post2.type = Post.TYPE_POST
        post2.featured_note = True
        post2.save()

        post = Post.objects.featured_review()
        self.assertEqual(post.permalink, u'third-post')

        # change featured post status and check if cache is invalidated
        post2 = Post.objects.get(title__iexact='third post')
        post2.status = Post.DRAFT_STATUS
        post2.save()

        post = Post.objects.featured_review()
        self.assertEqual(post.permalink, u'second-post')

        # republished post
        post2 = Post.objects.get(title__iexact='third post')
        post2.status = Post.PUBLIC_STATUS
        post2.save()

        post = Post.objects.featured_review()
        self.assertEqual(post.permalink, u'third-post')
        self.assertEqual(Post.objects.recent_reviews().count(), 0)

    def test_tagging( self ):
        """
            test posts tagging
        """

        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.body = "siala lala tralala"
        post.user = self.u1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.tag_list = 'ww2,pl,lorem'
        post.save()

        self.assertEqual( UserActivity.objects.all_notes().tagged( 'ww2' ).count(), 1 )

    def test_related_movies( self ):
        """
            test post related movies
        """

        self.assertEqual( Post.objects.count(), 0 )

        params = { 
            "title"       : "Battlefield review",
            "body"        : "Lorem ipsum",
            "publish"     : "1",
            "related_film": "Battlefield Earth II [2010],"
        }
        
        self.client.login( username='michuk', password='secret' )
        response = self.client.post( reverse( 'new_article' ), params, follow=True )
        
        self.assertEqual( response.status_code, 200 )
        self.assertEqual( Post.objects.count(), 1 )

        post = Post.objects.all()[0]

        self.assertEqual( post.title, params['title'] )
        
        self.assertEqual( UserActivity.objects.count(), 1 )

        act = UserActivity.objects.all()[0]

        if settings.SOLR_TESTS:
            self.assertEqual( post.related_film.count(), 1 )
            self.assertFalse( act.film is None )
            self.assertEqual( act.film_title, self.film.get_title() )
            self.assertEqual( act.film_permalink, self.film.permalink )

        # edit article
        params['related_film'] = ''
        response = self.client.post( reverse( 'edit_article', args=[post.pk] ), params, follow=True )
        
        self.assertEqual( response.status_code, 200 )
        self.assertEqual( Post.objects.count(), 1 )

        post = Post.objects.all()[0]

        self.assertEqual( post.related_film.count(), 0 )
        
        self.assertEqual( UserActivity.objects.count(), 1 )

        act = UserActivity.objects.all()[0]

        self.assertTrue( act.film is None  )
        self.assertTrue( act.film_title is None  )
        self.assertTrue( act.film_permalink is None  )


