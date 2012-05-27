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
from datetime import datetime

import logging
from django.db import models
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django.contrib.contenttypes import generic
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse

LANGUAGE_CODE = settings.LANGUAGE_CODE

from film20.core.models import Film, Object, Person, Profile
from film20.core.urlresolvers import make_absolute_url
from film20.config.urls import *
from film20.utils.slughifi import slughifi
from film20.tagging.models import TaggedItem, Tag
from film20.utils import cache_helper as cache
from film20.utils.cache_helper import CACHE_ACTIVITIES, KEY_FEATURED, KEY_RECENT

logger = logging.getLogger(__name__)
#from film20.pingback.client import execute_dirs_ping

DOMAIN = settings.DOMAIN
FULL_DOMAIN = settings.FULL_DOMAIN
SUBDOMAIN_AUTHORS = settings.SUBDOMAIN_AUTHORS

# Create your models here.
class BlogManager(models.Manager):
    
    # overridden method for FLM-707
    def get_query_set(self):
        return super(BlogManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)  

class Blog(models.Model):
    
    objects = BlogManager()
    
    user = models.ForeignKey(User, related_name="blog_owner", null=True, blank=True)
    title = models.CharField(_('Blog title'), max_length=200, blank=True)
    
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    def __unicode__(self):
        return "%s" % self.user

    def get_absolute_url(self):
        the_url = ""

        if SUBDOMAIN_AUTHORS:
            the_url += "http://"+ unicode(self.user) + "." + DOMAIN + "/"
        else:
            the_url += "/"+ urls['SHOW_PROFILE'] +"/" + unicode(self.user) +"/"

        return the_url

    def get_absolute_url_old_style(self):
        return self.get_absolute_url()

class PostManager(models.Manager):
    
    # overridden method for FLM-707
    def get_query_set(self):
        return super(PostManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)

    def all_for_user(self, user):
        """
            Return all posts for user (including drafts)
        """

        posts = Post.objects.filter(
            Q(user = user),
            Q(status = Post.PUBLIC_STATUS)|
            Q(status = Post.DRAFT_STATUS)
        )

        posts.order_by('-publish')

        return posts

    def public_for_user(self, user):
        """
            Return all public posts for user
        """

        posts = Post.objects.filter(user = user,
            status = Post.PUBLIC_STATUS
            )

        posts.order_by('-publish')

        return posts

    def recent_reviews(self):
        recent_reviews = cache.get_cache(CACHE_ACTIVITIES, KEY_RECENT)
        if not recent_reviews:
            recent_reviews = Post.objects.select_related('parent', 'user').filter(featured_note=False, is_published=True, status=Post.PUBLIC_STATUS)\
                                     .exclude(featured_note=True).order_by("-publish")[:settings.NUMBER_OF_REVIEWS_FRONT_PAGE]
            cache.set_cache(CACHE_ACTIVITIES, KEY_RECENT, recent_reviews)
        return recent_reviews

    def featured_review(self):
        featured_review = cache.get_cache(CACHE_ACTIVITIES, KEY_FEATURED)
        if not featured_review:
            featured_reviews = Post.objects.select_related('parent', 'user').filter(featured_note=True, is_published=False, status=Post.PUBLIC_STATUS)\
                                       .exclude(is_published=True).order_by("-publish")[:1]
            if len(featured_reviews)!=0:
                featured_review = featured_reviews[0]
            cache.set_cache(CACHE_ACTIVITIES, KEY_FEATURED, featured_review)
        return featured_review

class Post(Object):
    
    objects = PostManager()
    
    title = models.CharField(_('Title'), max_length=200)
    parent = models.OneToOneField(Object, parent_link=True)
    user = models.ForeignKey(User)
    creator_ip = models.IPAddressField(_('IP Address of the Post Creator'), blank=True, null=True)
    lead = models.TextField(_('Lead'), blank=True)
    body = models.TextField(_('Body'))

    # date of publication (TODO: rename to publication_date or published_at)
    publish = models.DateTimeField(_('Publish'), blank=True, null=True)
    # if True=visible, if False: draft (TODO: possibly rename to is_visible)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(_('Created at'), default=datetime.now)
    updated_at = models.DateTimeField(_('Updated at'))
    related_film = models.ManyToManyField(Film, related_name="related_film", null=True, blank=True, )
    related_person = models.ManyToManyField(Person, related_name="related_people", null=True, blank=True,)  

    # True if set to review of the date
    featured_note = models.BooleanField(_('Review of the day'), default=False)
    # True if set to "promoted on the main page and in most interesting posts"
    is_published = models.BooleanField(_('Is published'), default=False)
    # Whether or not it contains spoilers
    spoilers = models.BooleanField(_('Spoilers'), default=False)
        
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    
    temp_related_film = [] # this is for FLM-1206

    # tagging ...
    tag_list = models.CharField( max_length=255, null=True, blank=True )
    tagged_items = generic.GenericRelation( TaggedItem,
                                   content_type_field='content_type',
                                   object_id_field='object_id' )

    def _get_tags( self ):
        return Tag.objects.get_for_object( self )

    def _set_tags( self, tag_list ):
        Tag.objects.update_tags( self, tag_list )
        
    def get_tags_as_string( self ):
        return ', '.join( t.name for t in self.tags )

    tags = property(_get_tags, _set_tags)
   

    def __unicode__(self):
        return self.title
    
    class Meta:
        get_latest_by = 'publish'
        ordering = ('-publish',)
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def get_absolute_url(self):
        return make_absolute_url(self.get_slug())

    def get_absolute_url_old_style(self):
        the_url = ""
        if SUBDOMAIN_AUTHORS:
            the_url = "http://" + unicode(self.user.username) + "." + settings.DOMAIN_OLD + "/"
        else:
            the_url = settings.FULL_DOMAIN_OLD + "/" + urls['SHOW_PROFILE'] +"/" + unicode(self.user.username) +"/"
        the_url += urls['BLOG_POST_OLD'] + "/" + self.permalink + "/"
        return the_url

    def get_slug(self):
        return reverse('show_article', args=[unicode(self.user), self.permalink])

    def get_feed_url(self):
        the_url = "/"+ urls['SHOW_PROFILE'] +"/" + unicode(self.user) +"/" + urls['RSS'] + "/"
        return the_url

    main_related_film = None

    def get_main_related_film(self):
        cache_key = cache.Key('film_related', self.permalink)
        self.main_related_film = cache.get(cache_key)
        if not self.main_related_film:
            all_related_films= Film.objects.filter(id__in=self.related_film.all())
            if all_related_films:
                if len(all_related_films) == 1:
                    self.main_related_film = all_related_films[0]
            cache.set(cache_key, self.main_related_film)
        return self.main_related_film

    def save(self, permalink=None, *args, **kwargs):
        self.updated_at = datetime.now()
        self.type = Object.TYPE_POST

        if self.permalink is None or self.permalink == '':
            self.permalink = slughifi(self.title) # FLM-164
        # case: we're publishing the article, i.e. making it publicly visible
        if self.is_public == False and self.status == Post.PUBLIC_STATUS:
            self.is_public = True
            # only update published date if this hasn't been published before
            if self.publish is None:
                self.publish = datetime.now()
#            PingbackNote(note=self).save()
        # case: we're unpublishing the article, i.e. making it invisible again
        elif self.is_public == True and self.status == Post.DRAFT_STATUS:
            self.is_public = False
        # case: we're updating an already public article
        elif self.is_public == True:
            pass
        # case: we're updating a draft article, no need to create/update activity
        else:
            pass

        # fetch from post changes: featured, published or status
        try:
            orig = Post.objects.get(id=self.pk)
            featured_note = orig.featured_note
            is_published = orig.is_published
            status = orig.status
        except:
            featured_note = None
            is_published = None
            status = None

        # if we have featured or publish post check it status changes
        status_featured_changed = False
        status_published_changed = False
        if self.featured_note:
            if self.status != status:
                status_featured_changed = True

        if self.is_published:
            if self.status != status:
                status_published_changed = True

        # invalidate cache
        if self.featured_note != featured_note or status_featured_changed:
            cache.delete_cache(CACHE_ACTIVITIES, KEY_FEATURED)
        if self.is_published != is_published or status_published_changed:
            cache.delete_cache(CACHE_ACTIVITIES, KEY_RECENT)

        super(Post, self).save(*args, **kwargs)
        self.tags = self.tag_list

        if self.status == Post.DELETED_STATUS:
            from film20.threadedcomments.models import ThreadedComment
            ThreadedComment.objects.delete_for_object(self.id)

        self.save_activity()

    def get_title(self):
        return self.title

    def get_comment_title(self):
        title = self.get_title()
        title += " ("+ unicode(self.user) +")"
        return title

    def get_absolute_url_edit_comment(self, comment_id):
        the_url = self.get_absolute_url()
        the_url += '/' + urls['EDIT_COMMENT']+'/' + unicode(comment_id) + "/"
        return the_url

    def save_activity(self, status=None, *args, **kwargs):
        """
            Creates or updates an activity related to this article
        """
        from film20.useractivity.models import UserActivity
        act = None
        # Checking if activity already exists for the given article, 
        # if so update activity
        try:
            act = UserActivity.objects.get(post = self, user = self.user)
        # otherwise, create a new one
        except UserActivity.DoesNotExist:
            act = UserActivity()
            act.user = self.user
            act.activity_type = UserActivity.TYPE_POST
            act.post = self

        act.title = self.get_title()

        if self.lead:
            act.content = self.lead
        else:
            act.content = self.body

        rf = self.related_film.all()
        # special case: one film related with article - article is a review
        if len(rf) == 1:
            act.film_title = rf[0].get_title()
            act.film = rf[0]
            act.film_permalink = rf[0].permalink
        else:
            act.film = None
            act.film_title = None
            act.film_permalink = None
        act.username = self.user.username
        act.spoilers = self.spoilers
        act.status = self.status
        act.permalink = self.get_absolute_url() # legacy
        if self.featured_note or self.is_published:
            act.featured = True
        else:
            act.featured = False

        if self.publish is not None:
            act.created_at = self.publish
        act.save()
    
    def get_related_films(self):
        return self.related_film.all()

    MIN_NUMBER_OF_LIKES = int( getattr( settings, "POST_MIN_NUMBER_OF_LIKES", "2" ) )
    @classmethod
    def count_likes( cls, sender, instance, created, *args, **kwargs ):
        if isinstance( instance.object, cls ) \
            and len( instance.object.get_related_films() ) \
            and instance.total_count >= cls.MIN_NUMBER_OF_LIKES:
                instance.object.is_published = True
                instance.object.save()

class PingbackNote(models.Model):
    note = models.ForeignKey(Post, related_name="note_to_ping")
    is_ping = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%s' % (self.note)

from django.db.models.signals import post_save
from film20.core.models import parse_for_nicknames
from film20.facebook_connect.models import LikeCounter

post_save.connect( parse_for_nicknames, sender=Post, dispatch_uid="post__post_save___parse_for_nicknames" )
post_save.connect( Post.count_likes, sender=LikeCounter, dispatch_uid="post__post_save___count_likes" )
