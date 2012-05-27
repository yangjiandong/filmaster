from django.core import mail
from django.test.client import Client
from django.contrib.auth.models import User
from django.template import Context, Template
from django.utils.translation import gettext as _

from film20.blog.models import Post
from film20.utils.test import TestCase
from film20.core.models import Object, ShortReview
from film20.threadedcomments.models import ThreadedComment
from film20.core.templatetags.map_url import url_username_link as uul

class ParseNicknamesTestCase( TestCase ):

    def setUp( self ):
        self.user1 = User.objects.create_user( 'root', 'root@root.com', 'root' )
        self.user2 = User.objects.create_user( 'user', 'user@user.com', 'user' )
        self.user3 = User.objects.create_user( 'b_as', 'b_as@b_as.com', 'b_as' )

    def tearDown( self ):

        mail.outbox = []

        User.objects.all().delete()
        Post.objects.all().delete()
        ShortReview.objects.all().delete()
        ThreadedComment.objects.all().delete()

    def test_filter( self ):
       
        template = Template( '{% load parse_nicknames %}{{ text|parse_nicknames }}' )

        context = Context( { 'text': 'lorem ipsum @root sid at ble' } )
        self.assertEqual( template.render( context ), 'lorem ipsum <a href="%s" rel="nofollow">@root</a> sid at ble' % uul( 'root' )  )

        context = Context( { 'text': 'lorem ipsum @root,@toor sid at ble' } )
        self.assertEqual( template.render( context ), 
            'lorem ipsum <a href="%s" rel="nofollow">@root</a>,<a href="%s" rel="nofollow">@toor</a> sid at ble' \
                % ( uul( 'root' ), uul( 'toor' ) ) )

    def test_notifications( self ):
        
        mail.outbox = []

        wallpost = ShortReview()
        wallpost.user = self.user1
        wallpost.review_text = "lorem ipsum @user,@b_as sid at ble"
        wallpost.status = Object.PUBLIC_STATUS
        wallpost.kind = ShortReview.WALLPOST
        wallpost.type = Object.TYPE_SHORT_REVIEW
        wallpost.save()

        self.assertEqual( len( mail.outbox ), 2 )
        self.assertTrue( wallpost.get_absolute_url() in mail.outbox[0].body )
        
        print mail.outbox[0].body

        mail.outbox = []

        comment = ThreadedComment.objects.create_for_object( wallpost, user=self.user2, 
                                ip_address='127.0.0.1',comment="test comment @root",
                                status=ThreadedComment.PUBLIC_STATUS, type = ThreadedComment.TYPE_COMMENT )

        self.assertEqual( len( mail.outbox ), 1 )
        self.assertTrue( comment.get_absolute_url() in mail.outbox[0].body )
        
        print mail.outbox[0].body

        mail.outbox = []

        post = Post()
        post.title = "Lorem ipsum"
        post.permalink = "lorem-ipsum"
        post.lead = "lorem-ipsuam @root"
        post.body = "siala lala tralala @b_as"
        post.user = self.user1
        post.status = Object.PUBLIC_STATUS
        post.type = Object.TYPE_POST
        post.save()

        self.assertEqual( len( mail.outbox ), 2 )
        self.assertTrue( post.get_absolute_url() in mail.outbox[0].body )
        
        print mail.outbox[0].body

