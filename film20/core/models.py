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
from django.utils.translation import gettext_lazy as _, gettext
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models, transaction
from django.db.models import Manager, Q, Avg
from django.db.models.signals import post_save, pre_save, post_delete

from django.contrib.auth.models import User, AnonymousUser
from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.contenttypes import generic

from django.dispatch import receiver

from film20.userprofile.models import Avatar
from film20.tagging.models import Tag
from film20.config.urls import *
from film20.utils.utils import needle_in_haystack
from film20.utils.texts import *

from film20.utils import cache
from film20.utils.cache_helper import cache_query
from film20.utils.functional import memoize_method
from film20.utils.db import QuerySet, LangQuerySet, FieldChangeDetectorMixin, InstanceCache, Model
from film20.core.urlresolvers import reverse as abs_reverse, make_absolute_url
from film20.core.deferred import defer

from film20.moderation.registry import registry, AlreadyRegistered
from film20.moderation.models import ModeratedObject
from film20.moderation.items import ModeratedObjectItem
from film20.moderation.utils import html_diff

import re
import random
import datetime
import json, hashlib, os, time

from decimal import Decimal

import logging
logger = logging.getLogger(__name__)

LANGUAGE_CODE = settings.LANGUAGE_CODE
COUNTRY = settings.COUNTRY
DOMAIN = settings.DOMAIN
FULL_DOMAIN = settings.FULL_DOMAIN
SUBDOMAIN_AUTHORS = settings.SUBDOMAIN_AUTHORS

# constants
SAVED_BY_USER = 1
SAVED_BY_FETCHER = 2

class CaseInsensitiveQuerySet(QuerySet):
    def _filter_or_exclude(self, mapper, *args, **kwargs):
        # 'name' is a field in your Model whose lookups you want case-insensitive by default
        if 'name' in kwargs:
            kwargs['name__iexact'] = kwargs['name']
            del kwargs['name']
        return super(CaseInsensitiveQuerySet, self)._filter_or_exclude(mapper, *args, **kwargs)

class Object(Model, InstanceCache):
    
    TYPE_FILM = 1
    TYPE_PERSON = 2
    TYPE_POST = 3
    TYPE_SHORT_REVIEW = 4
    TYPE_FORUM = 5
    TYPE_EVENT = 6
    TYPE_THREAD = 7
    TYPE_LINK = 8
    TYPE_COMMENT = 9
    TYPE_FESTIVAL = 10
    TYPE_CONTEST = 11
    TYPE_GAME = 12
    
    PUBLIC_STATUS = 1
    DRAFT_STATUS = 2
    DELETED_STATUS = 3
    
    OBJECT_TYPE_CHOICES = (
        (TYPE_FILM, 'Film'),
        (TYPE_PERSON, 'Person'),
        (TYPE_POST, 'Post'),
        (TYPE_SHORT_REVIEW, 'Short Review'),
        (TYPE_FORUM, 'Forum'),
        (TYPE_EVENT, 'Event'),
        (TYPE_THREAD, 'Thread'), # only hostorical objects, deprecated since 2.0
        (TYPE_LINK, 'Link'),
        (TYPE_COMMENT, 'Comment'),
        (TYPE_FESTIVAL, 'Festival'),
        (TYPE_CONTEST, 'Contest'),
        (TYPE_GAME, 'Game')
    )

    OBJECT_STATUS_CHOICES = (
        (DRAFT_STATUS, _('Draft')),
        (PUBLIC_STATUS, _('Public')),
        (DELETED_STATUS, _('Deleted')),
    )
    
    type = models.IntegerField(choices=OBJECT_TYPE_CHOICES)
    permalink = models.CharField(max_length=128)
    status = models.IntegerField(choices=OBJECT_STATUS_CHOICES, default=PUBLIC_STATUS)    
    version = models.IntegerField()
    number_of_comments = models.IntegerField(blank=True, null=True)
    
    class Meta:
        permissions = (
            ("can_skip_cache", "Can skip cache"),
        )
    
    def save(self, *args, **kwargs):
        """
            Increment Object version when saved
        """
        if self.version == None:
            self.version = 1
        else:
            self.version = self.version + 1        

        if self.status == None:
            self.status = 1
        super(Object, self).save(*args, **kwargs)
        
        
    #def save_searchkeys(self, text):
    #    self.searchkey_set.filter(object_localized=None).delete()
    #    create_searchkeys(text, self.searchkey_set)
    # TODO: create Manager and make default query ignore status == 0     
        
    # TODO: get rid of this hack or properly throw exceptions here
    def get_film(self):
        if self.type==Object.TYPE_FILM:
            try:
                key = cache.Key(cache.CACHE_FILM, self.permalink)
                # try to retrieve from cache
                result = cache.get(key)
                if result!=None:
                    return result
                result = Film.objects.select_related().get(parent__permalink=self.permalink) 
                
                # store in cache
                cache.set(key, result)
        
                return result
            except Film.DoesNotExist:            
                return None
        return None

    def get_child_absolute_url(self):
        """
           Helper method to call get_absolute_url() for the child object in hierarhy.
           This should NOT be used if we have a reference to the child object (like Post/Film/Person)
           as it generates an additional database query to get the object.
        """
        if self.type == Object.TYPE_PERSON:
            return Person.objects.get(id=self.id).get_absolute_url() 
        elif self.type == Object.TYPE_FILM:
            return Film.objects.get(id=self.id).get_absolute_url() 
        elif self.type == Object.TYPE_FESTIVAL:
            from film20.festivals.models import Festival
            return Festival.objects.get(id=self.id).get_absolute_url() 
        elif self.type == Object.TYPE_POST:
            from film20.blog.models import Post
            return Post.objects.get(id=self.id).get_absolute_url() 
        elif self.type == Object.TYPE_SHORT_REVIEW:
            return ShortReview.objects.get(id=self.id).get_absolute_url() 
        
    def get_absolute_url_with_comment(self, comment_id):
        """
            Calls the default get_absolute_url method and adds comment ID at the end of it
            To be used for Post, ShortReview objects
            (and possibly more commentable objects in the future)
        """
        the_url = self.get_absolute_url()
        the_url += "#" + unicode(comment_id)
        return the_url

    def get_slug(self):
        """
            To be overwritten in children models
        """
        raise NotImplementedError()

    def __unicode__(self):
        return '%s' % (str(self.id) + " [" + self.permalink + "]")
   
    def get_similar_users_ratings(self, user, number):
        similar_users_list = user.followers.similar_users(number)
        ratings = self.get_ratings()
        ratings = ratings.filter(user__in = similar_users_list)
        return ratings
    
    def get_friends_ratings(self, user):
        ratings = self.get_ratings()
        ratings = ratings.filter(
            user__to_users__from_user=user,
            user__to_users__status=1).order_by('user__to_users__created_at')[:settings.NUMBER_OF_FRIENDS_RATINGS]
        return ratings
 
    def get_ratings(self):
        ratings = Rating.objects.select_related().filter(parent=self, type=1,
                                                         rating__isnull=False)\
                         .exclude(user__username__startswith='tmp-')\
                         .order_by('-last_rated')
        return ratings

    def get_localized_object(self, lang=LANGUAGE_CODE):

        property_name = '_object_localized_%s' % lang
        if hasattr( self, property_name ):
            return getattr( self, property_name )

        key = cache.Key( "localized_object", self.id, lang )
        object_localized = cache.get( key )

        if object_localized is None:
            try:
                object_localized = ObjectLocalized.objects.get( parent=self.id, LANG=lang )
            except ObjectLocalized.DoesNotExist:            
                object_localized = False
            cache.set( key, object_localized )
        
        setattr( self, property_name, object_localized )
        return object_localized

    def set_localized_object( self, localized, lang=LANGUAGE_CODE  ):
        cache.set( cache.Key( "localized_object", self.id, lang ), localized )
        setattr( self, "_object_localized_%s" % lang, localized )
        
    localized_object = property(fget=get_localized_object, fset=set_localized_object)

    @property
    def poster( self ):
        return Poster.objects.get_image( self )

    def get_image( self, x, y='auto' ):
        from film20.utils.posters import get_image_path
        return get_image_path( self, x, y )

    @property
    def posters( self ):
        main = Poster.objects.get_poster( self )
        posters = Poster.objects.filter( object=self )
        if main is not None:
            posters = posters.exclude( pk=main.pk )
        return posters

    def clean_instance_cache_kwargs(self):
        return dict(id=self.id), dict(permalink=self.permalink)

class ObjectAdmin(admin.ModelAdmin):
    search_fields = ('permalink',)
    
def image_path(prefix):
    def get_image_path(instance, filename):
        h = hash(filename) & 0xffff
        if isinstance(instance, Film):
            t = 'f'
        elif isinstance(instance, Person):
            t = 'p'
        else:
            t = 'o'
        return '%s/%s/%02x/%02x/%s' % (prefix, t, h >> 8, h & 0xff, filename)
    return get_image_path

def get_imdb_image_path(instance, filename):
    return 'img/objects/%s/%s' % (filename[0], filename)

from film20.utils.db.fields import ThumbImageField
class IMDBObject(Object):

    # TODO: need to remove after posters migration    
    image = models.ImageField(upload_to=get_imdb_image_path, null=True, blank=True)
    hires_image = models.ImageField(upload_to=image_path('img/obj'), null=True, blank=True, max_length=256)
    # ...

    imdb_code = models.CharField(max_length=128, null=True, blank=True, unique = True)
    parent = models.OneToOneField(Object, parent_link=True)

    # fixes for tmdb poster fetcher
    NOT_IMPORTED = 0
    IMPORTED = 1
    IMPORTED_TMDB = 1
    IMPORTED_IMDB = 2
    IMPORTED_IMDB_LOWRES = 3
    IMPORT_FAILED_NO_POSTER = -1
    IMPORT_FAILED_NO_OBJECT_IN_DB = -2
    IMPORT_FAILED_OTHER_REASON = -3

    TMDB_IMPORT_CHOICES = (
        (NOT_IMPORTED, "Not imported"),
        (IMPORTED_TMDB, "Imported - TMDB"),
        (IMPORTED_IMDB, "Imported - IMDB"),
        (IMPORTED_IMDB_LOWRES, "Imported - IMDB lowres"),
        (IMPORT_FAILED_NO_POSTER, "Import failed no poster"),
        (IMPORT_FAILED_NO_OBJECT_IN_DB, "Import failed no object in db"),
        (IMPORT_FAILED_OTHER_REASON, "Import failed other reason")
    )

    tmdb_import_status = models.IntegerField(choices=TMDB_IMPORT_CHOICES, default=NOT_IMPORTED)

    def __init__(self, *args, **kw):
        """
        nasty hack to eliminate db hit when film.parent is accessed
        """
        super(IMDBObject, self).__init__(*args, **kw)
#        if self.id :
#            self.parent = Object(*(getattr(self, f.name) for f in Object._meta.fields))
    
    def get_tags(self, lang=LANGUAGE_CODE):
        localized = self.get_localized_object( lang )
        return localized and localized.tag_list or ''

    def get_tag_list(self):
        lo = self.get_localized_object()
        tags = lo and Tag.objects.get_for_object(lo).values_list('name', flat=True) or ()
        return tags
        
    def save_tags(self, tags, LANG=LANGUAGE_CODE):        
        """
            Saves tags for the current localized object connected with the IMDBObject
        """
        try:
            object_localized = ObjectLocalized.objects.get(parent=self.parent, LANG=LANG)
        except ObjectLocalized.DoesNotExist:
            object_localized = ObjectLocalized(parent=self.parent)
            object_localized.LANG=LANG
            object_localized.save()

        object_localized.tag_list = tags
        object_localized.save()

        self.set_localized_object( object_localized, LANG )

    def save(self, saved_by=SAVED_BY_USER, *args, **kwargs):
        super(IMDBObject, self).save(*args, **kwargs)

        # http://jira.filmaster.org/browse/FLM-483
        # so that we don't have to inveng absurd IMDB codes if we're
        # adding a film manually (not in IMDB, yet)
        if (str(self.imdb_code)).strip() == '':
            self.imdb_code = None

    class Meta:
        abstract = True
    
    def get_absolute_image_url(self):
        if self.hires_image or self.image:
            return u"%s%s" % (settings.MEDIA_URL, self.hires_image or self.image)
        else:
            from film20.config import urls
            return urls.urls.get('DEFAULT_POSTER')
    
    def create_thumbnails(self):
        if self.hires_image and settings.CREATE_THUMBNAILS:
            from film20.utils.posters import make_thumbnail
            for size in settings.POSTER_THUMBNAIL_SIZES:
                make_thumbnail(self.hires_image, size)

class ProfileManager(models.Manager):
    pass
    
from film20.userprofile.models import BaseProfile
GENDER_CHOICES = ( ('F', _('Female')), ('M', _('Male')),)

class LocalizedProfileManager(models.Manager):
    def get_query_set(self):
        return super(LocalizedProfileManager, self).get_query_set().filter(LANG=LANGUAGE_CODE)
        
    @memoize_method
    def get_for(self, user):
        localized_profile, created = self.model.objects.get_or_create(
            user=user,
            LANG=LANGUAGE_CODE
        )
        return localized_profile

class LocalizedProfile(models.Model):
    user = models.ForeignKey(User)

    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    
    description = models.CharField(_('About you'), max_length=255, blank=True, null=True)
    blog_title = models.CharField(_('Blog title'), max_length=200, blank=True, null=True)

    objects = LocalizedProfileManager()

    class Meta:
        unique_together = ('user', 'LANG')

class Profile(FieldChangeDetectorMixin, BaseProfile):

    # Profile-specific fields
    gender = models.CharField(_('Gender'), max_length=1, choices=GENDER_CHOICES, blank=True)
    website = models.CharField(_('Website'), max_length=100, blank=True, null=True)

    # TODO - localized fields, can be removed after migration to LocalizedProfile
    description = models.CharField(_('About you'), max_length=255, blank=True, null=True)
    # end of localized fields
    
    twitter_access_token = models.CharField(max_length=256, null=True, blank=True)
    twitter_user_id = models.CharField(max_length=32, null=True, blank=True)
    foursquare_access_token = models.CharField(max_length=128, null=True, blank=True)
    foursquare_user_id = models.CharField(max_length=32, null=True, blank=True)
    
    # base64 encoded iphone token
    iphone_token = models.CharField(max_length=64, null=True, blank=True)
    
    mobile_platform = models.CharField(max_length=16, null=True, blank=True)
    mobile_first_login_at = models.DateTimeField(blank=True, null=True)
    mobile_last_login_at = models.DateTimeField(blank=True, null=True)
    mobile_login_cnt = models.IntegerField(default=0)
            
    jabber_id = models.CharField(_('Jabber ID'), max_length=50, blank=True, null=True)
    gg = models.CharField(_('Gadu-Gadu'), max_length=50, blank=True, null=True)
    msn = models.CharField(_('MSN'), max_length=50, blank=True, null=True)
    icq = models.CharField(_('ICQ'), max_length=50, blank=True, null=True)
    aol = models.CharField(_('AOL'), max_length=50, blank=True, null=True)
    phone_number = models.CharField(_("Phone number"), max_length=50, blank=True, null=True)
    facebook_name = models.CharField(_('Facebook'), max_length=50, blank=True, null=True)
    myspace_name = models.CharField(_('MySpace'), max_length=50, blank=True, null=True)
    criticker_name = models.CharField(_('Criticker'), max_length=50, blank=True, null=True)
    imdb_name = models.CharField(_('IMDB'), max_length=50, blank=True, null=True)
    metacritic_name = models.CharField(max_length=128, blank=True)

    # preferred language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    registration_source = models.CharField(max_length=255, null=True, blank=True)
    
    timezone_id = models.CharField(max_length=40, null=True, blank=True)

    # this is a hack for django-notifications: http://jira.filmaster.org/browse/FLM-306
    language = property(lambda self: self.LANG)

    NO_RECOMMENDATIONS = 0
    NORMAL_RECOMMENDATIONS = 1
    FAST_RECOMMENDATIONS_WAITING = 2
    FAST_RECOMMENDATIONS = 3

    RECOMMENDATIONS_STATUS_CHOICES = (
        (NO_RECOMMENDATIONS, _('No recommendations')),
        (NORMAL_RECOMMENDATIONS, _('Normal recommendations')),
        (FAST_RECOMMENDATIONS, _('Fast recommendations')),
        (FAST_RECOMMENDATIONS_WAITING, _('Waiting for fast recommendations')),
    )

    recommendations_status = models.IntegerField(default=NO_RECOMMENDATIONS, choices=RECOMMENDATIONS_STATUS_CHOICES)
    recommendations_notice_sent = models.IntegerField(default=0)

    # assign manager    
    objects = ProfileManager()
    all_profiles = models.Manager()

    DETECT_CHANGE_FIELDS = ('country', 'latitude', 'longitude', 'display_name')

    GOAL_RATE_15_FILMS = 0
    GOAL_VISIT_RECOMMENDATIONS = 1
    GOAL_UNKNOWN = 2

    current_goal = models.IntegerField(default=GOAL_RATE_15_FILMS)

    def has_location(self):
        return bool(self.latitude is not None and self.longitude is not None and (self.latitude or self.longitude))

    def has_recommendations(self):
        return self.recommendations_status in (Profile.NORMAL_RECOMMENDATIONS, Profile.FAST_RECOMMENDATIONS)

    def location_changed(self, geo):
        if not self.has_location() or not geo:
            return False
        from geonames import geo_distance
        source = geo.get('source')
        lat = geo.get('latitude')
        lng = geo.get('longitude')
        return source == 'html5' and \
                geo_distance(self.latitude, self.longitude, lat, lng) > settings.DISTANCE_THRESHOLD

    def get_localized_profile(self):
        return LocalizedProfile.objects.get_for(self.user)

    def has_avatar(self):
        try:
            avatar = Avatar.objects.get(user=self.user, valid=True)
            return True    
        except Avatar.DoesNotExist:
            return False 

    def get_absolute_url(self):
        return full_url("SHOW_PROFILE") + unicode(self.user.username) + "/"

    def get_absolute_url_old_style(self):
        return self.get_absolute_url()

    def __unicode__(self):
        return '%s (%s)' % (self.user.username, self.user.get_full_name())
    
    def set_iphone_token(self, token):
        if token:
            token = token.replace(' ', '+')
            for p in Profile.objects.filter(iphone_token=token):
                 if p.pk != self.pk:
                     p.iphone_token = None
                     p.save()
        self.iphone_token = token
    
    @property
    @memoize_method
    def facebook_association(self):
        from film20.facebook_connect.models import FBAssociation
        try:
            return FBAssociation.objects.get(user=self.user)
        except FBAssociation.DoesNotExist:
            pass
            
    def get_local_time(self):
        if self.timezone_id:
            import pytz
            tz = pytz.timezone(self.timezone_id)
            utcnow = datetime.datetime.utcnow()
            return pytz.utc.localize(utcnow).astimezone(tz).replace(tzinfo=None)
        else:
            return datetime.datetime.now()
    
    @property
    def timezone(self):
        import pytz
        return pytz.timezone(self.timezone_id)

    @classmethod
    def get_user_profile(cls, user):
        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user
            user = None
        key = cache.Key("user_profile", user_id)
        # TODO - temporary disabled profile caching
        # workaround for http://jira.filmaster.org/browse/FLM-1723
        profile = None # cache.get(key)
        if profile is None:
            profile, created = Profile.objects.get_or_create(user__id__exact=user_id, defaults=dict(user_id=user_id))
            if user:
                profile.user = user
            cache.set(key, profile)
            if created:
                logger.warning("profile created for user %s", user_id)
        return profile


    def get_current_display_name(self):
        return self.display_name or self.user.username

    def is_moderator( self ):
        l = lambda p: self.user.has_perm( p )
        return self.user.is_superuser or ( l( 'core.can_edit_tags' ) or l( 'core.can_edit_localized_title' ) or l( 'core.can_edit_description' ) )

    @property
    def is_temporary(self):
        return not self.user.is_active 

    @classmethod
    def pre_save(cls, sender, instance, *args, **kw):
        profiles = Profile.objects.filter(Q(display_name = instance.display_name) | Q(user__username = instance.display_name)).exclude(user = instance.user)
        if instance.is_field_changed('display_name'):
            if len(profiles) == 0:
                logger.info('changed display name for profile %s into %s' % (instance.user, instance.display_name))
            else:
                logger.warning("display name %s is used by %s. cannot change display name" % (instance.display_name, profiles))
                instance.display_name = instance.prev_value('display_name')

    @classmethod
    def user_post_save(cls, sender, instance, created, *args, **kw):
        if created:
            profile = Profile.objects.get_or_create(user=instance, LANG=LANGUAGE_CODE)[0]
            profile.save()
        else:
            cache.delete(cache.Key("user_profile", instance.id))

pre_save.connect(Profile.pre_save, sender=Profile)
post_save.connect(Profile.user_post_save, sender=User)

@memoize_method
def get_profile(self):
    return Profile.get_user_profile(self)

User.get_profile = get_profile

class ProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ['user', ]
    search_fields = ('user__username',)

class AbstractLog(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    version_timestamp = models.DateTimeField(auto_now_add=True)
    
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)     
    saved_by = models.IntegerField(default=SAVED_BY_USER)       
    
    comment = models.CharField(max_length=40000, blank=True, null=True)
    
    TYPE_BOT = 1
    TYPE_DEFAULT = 2
    TYPE_TAGS = 3
    TYPE_LOCALIZED_TITLE = 4
    TYPE_DESCRIPTION = 5
    
    OBJECT_TYPE_CHOICES = (
        (TYPE_BOT, 'Bot'),
        (TYPE_DEFAULT, 'Default'),
        (TYPE_TAGS, 'Tags'),
        (TYPE_LOCALIZED_TITLE, 'Title'),
        (TYPE_DESCRIPTION, 'Description'),
    )
    
    type = models.IntegerField(choices=OBJECT_TYPE_CHOICES)

    class Meta:
        abstract = True

def _rand_score():
    return Decimal(str((random.randrange(100) + 1)/10.0)).quantize(Decimal("0.1"))

class PersonQuerySet(QuerySet):
    def fetch_related(self):
        def _fetch(items, **kw):
            items = list(items)
            localized = PersonLocalized.objects.filter(person__in=[p.id for p in items])
            localized = dict((p.person_id, p) for p in localized)
            for p in items:
                p.set_localized_person(localized.get(p.id))
                yield p
        return self.postprocess(_fetch)

class Person(IMDBObject):
    
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)   
    day_of_birth = models.IntegerField(blank=True, null=True)
    month_of_birth = models.IntegerField(blank=True, null=True)
    year_of_birth = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    is_director = models.BooleanField()
    is_actor = models.BooleanField()
    is_writer = models.BooleanField()
    # number of ratings
    actor_popularity = models.IntegerField(default=0)
    director_popularity = models.IntegerField(default=0)
    writer_popularity = models.IntegerField(default=0)
    # number of ratings in last month
    actor_popularity_month = models.IntegerField(default=0)
    director_popularity_month = models.IntegerField(default=0)
    writer_popularity_month = models.IntegerField(default=0)

    verified_imdb_code = models.BooleanField(default=False)
    import_comment = models.TextField( blank=True, null=True )

    person_localized = None
    person_localized_exists = True

    objects = PersonQuerySet.as_manager()

    def get_absolute_url(self):
        return abs_reverse('show_person', args=[self.permalink])

    def get_absolute_url_old_style(self):
        return self.get_absolute_url()
    
    def get_localized_person(self, lang=LANGUAGE_CODE):
        if hasattr(self, '_localized_person'):
            return self._localized_person
        # try to retrieve from cache
        key = cache.Key(cache.CACHE_PERSON_LOCALIZED, self.id)
        result = cache.get(key)
        if result is None:
            try:
                result = PersonLocalized.objects.get(person=self.id, LANG=lang)
            except PersonLocalized.DoesNotExist:
                # False instead of None (will be stored in cache)
                result = False
            cache.set(key, result)
        self._localized_person = result
        return self._localized_person

    def set_localized_person(self, localized_person):
        self._localized_person = localized_person
        cache.set(cache.Key(cache.CACHE_PERSON_LOCALIZED, self.id), localized_person or False)

    def get_or_create_localized_person( self, lang=LANGUAGE_CODE ):
        pl = self.get_localized_person( lang )
        if not pl:
            pl, created = PersonLocalized.objects.get_or_create( parent=self, person=self, LANG=lang )
            self.set_localized_person( pl )
        return pl

    def get_localized_name(self):
        pl = self.get_localized_person()
        return pl and pl.name or self.name

    def set_localized_name( self, name ):
        pl = self.get_or_create_localized_person()
        pl.name = name
        pl.save()

    def get_localized_surname(self):
        pl = self.get_localized_person()
        return pl and pl.surname or self.surname

    def set_localized_surname( self, surname ):
        pl = self.get_or_create_localized_person()
        pl.surname = surname
        pl.save()

    def get_biography( self ):
        pl = self.get_localized_person()
        return pl and pl.biography or ''

    def set_biography( self, biography ):
        pl = self.get_or_create_localized_person()
        pl.biography = biography
        pl.save()

    localized_person = property(fget=get_localized_person, fset=set_localized_person)
    localized_name = property(fget=get_localized_name, fset=set_localized_name)
    localized_surname = property(fget=get_localized_surname, fset=set_localized_surname)
    biography = property( fget=get_biography, fset=set_biography )
        
        
    def save(self, saved_by=SAVED_BY_USER, *args, **kwargs):
        super(Person, self).save(*args, **kwargs)
        # Append FilmLog
        #super(Person, self).save_searchkeys(concatenate_words([self.name, self.surname]))
        self.save_log(saved_by=saved_by)
        
    def save_tags(self, tags, LANG=LANGUAGE_CODE, saved_by=SAVED_BY_USER):
        comment = "Old tags: [" + unicode(self.get_tags()) + "]"
        super(Person, self).save_tags(tags, LANG)
        comment += ", New tags: [" + unicode(tags) + "]"
        
        # Append PersonLog
        self.save_log(LANG, saved_by=saved_by, comment=comment, type=AbstractLog.TYPE_TAGS)
            
    def save_log(self, LANG=LANGUAGE_CODE, saved_by=SAVED_BY_USER, comment=None, type=AbstractLog.TYPE_DEFAULT):
        person_log = PersonLog(person=self, name=self.name, surname=self.surname, day_of_birth=self.day_of_birth,
                             month_of_birth=self.month_of_birth, year_of_birth=self.year_of_birth, 
                             gender=self.gender, is_director=self.is_director, is_actor=self.is_actor, 
                             actor_popularity=self.actor_popularity, director_popularity=self.director_popularity, 
                             actor_popularity_month=self.actor_popularity_month, director_popularity_month=self.director_popularity_month,
                             is_writer=self.is_writer, writer_popularity=self.writer_popularity, writer_popularity_month=self.writer_popularity_month)
        
        # from ObjectLocalized
        person_log.tag_list = self.get_tags(LANG)
        person_log.LANG = LANG
        person_log.save_by = saved_by
        # user
        from film20.middleware import threadlocals
        user = threadlocals.get_current_user()
        person_log.user = user if user and user.is_authenticated() else None
        if  person_log.user==None:
            person_log.type = AbstractLog.TYPE_BOT
        else:
            person_log.type = type
        
        person_log.comment = comment        
        
        person_log.save()
        logger.debug("Saving Person. ID=" + unicode(self.id) + ", Title: " + unicode(self.name) + " " + unicode(self.surname))

    def average_director_score(self):
        return Rating.objects.filter(director=self).\
                aggregate(Avg('rating'))['rating__avg']

    def average_actor_score(self):
        return Rating.objects.filter(actor=self).\
                aggregate(Avg('rating'))['rating__avg']

    def __unicode__(self):
        return '%s %s' % (self.name, self.surname)
        
    def format(self):
        return '%s %s' % (self.localized_name, self.localized_surname)

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')
        ordering = ["surname"]

class PersonAdmin(admin.ModelAdmin):
    search_fields = ('name', 'surname',)
    list_display = ('name', 'surname', 'imdb_code', 'import_comment', 'permalink', 'verified_imdb_code', 'acted')
    
    def acted( self, obj ):
        return ', '.join( [ '<a href="/admin/core/film/%d">%s</a>' % ( f.pk, f.get_title() ) for f in Film.objects.filter( character__person=obj ).distinct() ] )
    acted.allow_tags = True


class Country(models.Model):
    country = models.CharField( _("Country"), max_length=128, null=True, blank=True)
    
    def __unicode__(self):
        return self.country
    
class CountryAdmin(admin.ModelAdmin):
    list_display = ['country']

class FilmQuerySet(QuerySet):
    def get_by_same_director(self, film):
        return self.filter(directors_in=film.directors.all()).exclude(id=film.id).distinct()
   
    def tagged(self, tags):
        from film20.tagging.utils import parse_tag_input
        tags = parse_tag_input(tags.lower())
        return self.filter(objectlocalized__LANG=settings.LANGUAGE_CODE,
                           objectlocalized__tagged_items__tag__name__in=tags)

    def with_description(self):
        return self.filter(
                Q(filmlocalized__LANG=settings.LANGUAGE_CODE, filmlocalized__fetched_description__isnull=False) |
                Q(filmlocalized__LANG=settings.LANGUAGE_CODE, filmlocalized__description__isnull=False)
                )

    def with_poster(self):
        return self.exclude(hires_image='')

    def match(self, title, directors=None, year=None, limit=10):
        title_norm = normalized_text(title) or title

        query = self.distinct().order_by('-popularity')
        if year:
            query = query.filter(release_year__gte=int(year)-1, release_year__lte=int(year)+1)

        q1 = Q(title_normalized=title_norm)
        q2 = Q(filmlocalized__title_normalized=title_norm,
               filmlocalized__LANG=settings.LANGUAGE_CODE)

        films = query.filter(q1|q2)
        if limit:
            films = films[:limit]

        if directors:
            dset = set(normalized_text(d) for d in directors)
            def directors_match(film):
                film_directors = set()
                for d in film.directors.all():
                    film_directors.add(normalized_text(unicode(d)))
                    film_directors.add(normalized_text(d.format()))
                return film_directors & dset
            films = filter(directors_match, films)
        return films

class Film(IMDBObject):
    verified_imdb_code = models.BooleanField(default=False)
    import_comment = models.TextField( blank=True, null=True )
    
    title = models.CharField(max_length=128)
    title_normalized = models.CharField(max_length=128)
    criticker_id = models.CharField(max_length=16, null=True, blank=True)
    release_year = models.IntegerField()
    completion_year = models.IntegerField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    length = models.IntegerField(null=True, blank=True)
    
    # blank & null - potrzebne?
    directors = models.ManyToManyField(Person, related_name='films_directed', blank=True, null=True)    
    actors = models.ManyToManyField(Person, related_name='films_played', blank=True, null=True, through='Character')
    writers = models.ManyToManyField(Person, related_name='screenplays_written', blank=True, null=True)    
    production_country = models.ManyToManyField(Country, related_name='produced_in', blank=True, null=True)    
    production_country_list = models.CharField(max_length=256, blank=True, null=True)
    
    similar_films = models.ManyToManyField( 'self', through='SimilarFilm', symmetrical=False, related_name='similar_to' )
    
    # hack for ENH9
    is_enh9 = models.BooleanField()

    netflix_id = models.CharField(null=True, blank=True, max_length=128)
    netflix_instant = models.BooleanField(default=False)

    is_tv_series = models.BooleanField(default=False)

    objects = FilmQuerySet.as_manager()

    channels = ()
    
    #like_cnt = generic.GenericRelation(LikeCounter,
    #                               content_type_field='content_type',
    #                               object_id_field='object_id')

    def __hash__(self):
        if self.pk:
            return super(Film, self).__hash__()
        return hash(self.title)

    def __eq__(self, other):
        if not isinstance(other, Film): return False
        if self.pk or other.pk:
            return self.pk == other.pk
        return self.title == other.title

    def get_release_year(self):
        if not self.release_year:
            return ''
        if self.is_tv_series and self.completion_year and self.completion_year > self.release_year:
            return "%d-%d" % (self.release_year, self.completion_year)
        return "%d" % self.release_year

    def get_absolute_url(self):
        return abs_reverse('show_series' if self.is_tv_series else 'show_film', args=[self.permalink])

    def get_absolute_path(self):
        return reverse('show_series' if self.is_tv_series else 'show_film', args=[self.permalink])

    def get_absolute_url_old_style(self):
        return self.get_absolute_url()

    def title_in_current_locale(self):         
        haystack = self.production_country_list
        if not haystack:
            return False
        else:        
            needle = COUNTRY
            return needle_in_haystack(needle, haystack) 
    
    def get_title(self):
        """
            New get_title according to http://jira.filmaster.org/browse/FLM-319
            returns the localized title if it exists
            or the original title otherwise
        """
        if not self.pk:
            return self.title
        localized_film = self.get_localized_film()
        return localized_film and localized_film.title or self.title

    def get_both_titles(self):
        localized_film = self.get_localized_film()
        if localized_film:
            if localized_film.title:
                if self.title_in_current_locale():
                    return localized_film.title
                else:
                    return localized_film.title + " | " + self.title
        return self.title 
    
    def get_localized_film(self, lang=LANGUAGE_CODE):
        if hasattr(self, '_film_localized'):
            return self._film_localized
        key = cache.Key("film_localized_film", self.id, lang)
        self._film_localized = cache.get(key)
        if self._film_localized is None:
            try:
                self._film_localized = FilmLocalized.objects.get(film=self.id, LANG=lang)
            except FilmLocalized.DoesNotExist:            
                self._film_localized = False
            cache.set(key, self._film_localized)
        return self._film_localized
    
    def set_localized_film(self, localized):
        cache.set(cache.Key("film_localized_film", self.id, LANGUAGE_CODE), localized)
        self._film_localized = localized
        
    localized_film = property(fget=get_localized_film, fset=set_localized_film)
    
            
     # TODO: unit test to make sure core_object.permalink is fetched
    def get_directors(self):
        from film20.utils.cache import cache_query
        return cache_query(self.directors.all(), "film_directors", self)
    top_directors = get_directors
    
    def get_actors(self, LANG=LANGUAGE_CODE):
        return cache_query(self.character_set.select_related('person').\
                filter(LANG=LANG, person__isnull=False).\
                order_by("importance"), "film_actors", self)
    
    @memoize_method
    def get_release_date(self, country_code=None):
        if country_code:
            try:
                info = FilmCountryInfo.get(film=self, country_code=country_code)
                print info.release_date
                return info.release_date
            except FilmCountryInfo.DoesNotExist, e:
                pass
        else:
            return self.release_date

    # TODO: unit test to make sure core_object.permalink is fetched
    def top_actors(self, how_many_actors_to_show=10):
        return self.get_actors()[:how_many_actors_to_show]

    @property
    def imdb_link( self ):
        return 'http://www.imdb.com/title/tt%s' % self.imdb_code if self.imdb_code else None

    def save_tags(self, tags, LANG=LANGUAGE_CODE, saved_by=SAVED_BY_USER):
        comment = "Old tags: [" + unicode(self.get_tags()) + "]"
        super(Film, self).save_tags(tags, LANG)
        comment += ", New tags: [" + unicode(tags) + "]"
        
        # Append FilmLog
        self.save_log(LANG, saved_by=saved_by, comment=comment, type=AbstractLog.TYPE_TAGS)
        
    def get_localized_title(self, lang=LANGUAGE_CODE):
        localized = self.get_localized_film()
        return localized and localized.title or ''
    
    def get_or_create_film_localized(self, LANG):
        try:
            self._film_localized = FilmLocalized.objects.get(parent=self.parent, film=self.id, LANG=LANG)
        except FilmLocalized.DoesNotExist:
            try:
                object_localized = ObjectLocalized.objects.get(parent=self.parent, LANG=LANG)
            except ObjectLocalized.DoesNotExist:
                object_localized = ObjectLocalized(parent=self.parent, LANG=LANG)
                object_localized.save()
            self._film_localized = FilmLocalized(object_localized=object_localized, parent=self.parent, film=self, LANG=LANG)
            self._film_localized.tag_list = object_localized.tag_list
            self._film_localized.save()
        return self._film_localized
    
    def save_localized_title(self, localized_title, LANG=LANGUAGE_CODE, saved_by=SAVED_BY_USER):
        """
            Saves localized title for the current localized object connected with the Film object
        """
        
        if not getattr(self, 'film_localized', None):
            self.get_or_create_film_localized(LANG)
        elif self._film_localized.LANG!=LANG:
            self.get_or_create_film_localized(LANG)            
        
        comment = "Old title: [" + unicode(self._film_localized.title) + "]"            
        self._film_localized.title = localized_title
        comment += ", New title: [" + unicode(localized_title) + "]"
        self._film_localized.save()
        
        # Append FilmLog
        self.save_log(LANG, saved_by= saved_by, comment=comment, type=AbstractLog.TYPE_LOCALIZED_TITLE)        
        
    def get_description(self):
        localized = self.get_localized_film()
        out = localized and (localized.description or localized.fetched_description) or ''
        return self.DESCR_REPLACES.sub('', out)
    
    DESCR_REPLACES = re.compile(r'\s*\[(opis dystrybutora|dystrybutor)\]\s*')
    
    def set_description(self, description):
        return self.save_description(description)
    
    def save_description(self, description, LANG=LANGUAGE_CODE, saved_by=SAVED_BY_USER):
        """
            Saves localized description for the current localized object connected with the Film object
        """
        
        if not getattr(self, '_film_localized', None):
            self.get_or_create_film_localized(LANG)
        elif self._film_localized.LANG!=LANG:
            self.get_or_create_film_localized(LANG)    
                    
        comment = "Old description: [" + unicode(self._film_localized.description) + "]"            
        self._film_localized.description = description
        comment += ", New description: [" + unicode(description) + "]"
        
        self._film_localized.save()
        
        # Append FilmLog
        self.save_log(LANG, saved_by=saved_by, comment=comment, type=AbstractLog.TYPE_DESCRIPTION)        
    
    description = property(get_description, set_description)
    
    # number of ratings
    popularity = models.IntegerField(default=0)
    # number of ratings in last month
    popularity_month = models.IntegerField(default=0)
    
    def __unicode__(self):
        release_year = self.get_release_year()
        return self.get_title() + (release_year and " [%s]" % release_year or '')

    class Meta:
        verbose_name = _('Film')
        verbose_name_plural = _('Films')
        permissions = (
            ("can_edit_localized_title", "Can edit localized title"),
            ("can_edit_tags", "Can edit tags"),
            ("can_edit_description", "Can edit description"),
        )
        
    #def save_searchkeys(self):
    #    super(Film, self).save_searchkeys(self.title)
 
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.is_tv_series and not self.completion_year:
            raise ValidationError( _( 'Completion year is required for TV series.' ) )

    def save(self, saved_by=SAVED_BY_USER, *args, **kwargs):
        self.title_normalized = normalized_text(self.title) or self.title
        #self.title_root = string_root_normalized(self.title_normalized)    
        super(Film, self).save(*args, **kwargs)
        #self.save_searchkeys()
        # Append FilmLog
        self.save_log(saved_by=saved_by)
        
    def save_log(self, LANG=LANGUAGE_CODE, saved_by=SAVED_BY_USER, comment=None, type=AbstractLog.TYPE_DEFAULT):
        film_log = FilmLog(film=self, title=self.title, release_year=self.release_year, release_date=self.release_date)
        
        # from FilmLocalized
        film_log.localized_title = self.get_localized_title(LANG)
        film_log.tag_list = self.get_tags(LANG)
        film_log.LANG = LANG
        film_log.saved_by = saved_by
        
        # user / if no user, set edit type to bot
        from film20.middleware import threadlocals
        user = threadlocals.get_current_user()
        film_log.user = user if user and user.is_authenticated() else None
        if film_log.user==None:
            film_log.type = AbstractLog.TYPE_BOT
        else:
            film_log.type = type   
        film_log.comment = comment
        
        film_log.save()
        logger.debug("Saving Film. ID=" + unicode(self.id) + ", Title: " + unicode(self.title))

    @memoize_method
    def get_ranking(self):
        cache_key = cache.Key('film_rankings', self.permalink)
        ranking = cache.get(cache_key)
        if ranking is None:
            ret = self.filmranking_set.filter(type=Rating.TYPE_FILM)[:1]
            ranking = ret and ret[0] or False
            cache.set(cache_key, ranking)
        return ranking

    def average_score(self):
        if hasattr(self, '_average_score'):
            return self._average_score
        ranking = self.get_ranking()
        return ranking and ranking.average_score
    
    def number_of_votes(self):
        if hasattr(self, '_number_of_votes'):
            return self._number_of_votes
        ranking = self.get_ranking()
        return ranking and ranking.number_of_votes

    def get_videos(self):
        return Trailer.objects.get_for_object( self )

    def get_links(self):
        from film20.externallink.models import ExternalLink
        query = (Q(url_kind=ExternalLink.REVIEW) | 
                 Q(url_kind=ExternalLink.BOOK) | 
                 Q(url_kind=ExternalLink.NEWS)
                ) & Q(status=ExternalLink.PUBLIC_STATUS)
        return self.film_link.filter(query).order_by('-created_at')\
               .filter(LANG=settings.LANGUAGE_CODE)

    def get_related_films(self, min_score=Decimal(getattr(settings,
                    'MIN_FILM_COMPARATOR_SCORE'))):
        return Film.objects.filter(compared_films__main_film=self,
                                   compared_films__score__gte=min_score).\
                    exclude(id=self.id).order_by('-compared_films__score')

    @classmethod
    def get_film_ids_by_tag(cls, tag='', lang='pl'):
        """ Returns dict(id, popularity) for films with given tag"""

        key = cache.Key("films_by_tag", tag, lang)
        films = cache.get(key)
        if films is None:
            if tag:
                films = cls.objects.filter(
                        objectlocalized__tagged_items__tag__name=tag)
            else:
                films = cls.objects.all()

            if lang == 'en':
                films = films.exclude(production_country_list='Poland')
            films = films.order_by('-popularity')
            films = dict(films.values_list('parent_id', 'popularity'))
            cache.set(key, films)

        return films

    @classmethod
    def _to_rate_all_ids(cls, user, tag=''):
        if user.id:
            lang = user.get_profile().LANG
        else:
            lang = settings.LANGUAGE_CODE
        key = cache.Key("to_rate_all_ids", lang, tag)
        all_ids = cache.get(key)
        if all_ids is None:
            ranking = FilmRanking.objects.filter(type=Rating.TYPE_FILM)
            if lang == 'en':
                ranking = ranking.exclude(film__production_country_list='Poland')
            if tag:
                ranking = ranking.filter(
                        film__objectlocalized__tagged_items__tag__name=tag
                )
            ranking = ranking.order_by('-number_of_votes')
            all_ids = ranking.values_list('film_id', flat=True)
            cache.set(key, all_ids)
        return all_ids

    @classmethod
    def get_top_tags(cls, limit=settings.TOP_TAGS_NUMBER):
        key = cache.Key("top_tags", settings.LANGUAGE_CODE)
        tags = cache.get(key)
        if tags is None:
            tags = Tag.objects.filter(LANG=settings.LANGUAGE_CODE, items__content_type__model="objectlocalized")
            tags = tags.annotate(models.Count('items'))
            tags = tags.order_by('-items__count')[:limit]
            tags = list(tags)
            tags.sort(key=lambda x: x.name.lower())
            cache.set(key, tags)
        return tags 

    @property
    def is_short( self ):
        return 'short' in self.get_tags( lang='en' ).split(',')

    def last_check_in(self, user):
        from film20.showtimes.models import ScreeningCheckIn
        since = datetime.datetime.now() - datetime.timedelta(hours=1)
        s = ScreeningCheckIn.all_objects.filter(user=user, film=self, created_at__gte=since).order_by('-created_at')[0:1]
        return s and s[0] or None

    def check_in(self, user, status=None):
        from film20.showtimes.models import ScreeningCheckIn
        if status is None: status = ScreeningCheckIn.ACTIVE

        s = self.last_check_in(user)
        if s:
            if s.status != status:
                s.status = status
                s.save()
            return s

        if status == ScreeningCheckIn.ACTIVE:
            s = ScreeningCheckIn.objects.create(user=user, film=self)
        return s

    def check_in_cancel(self, user):
        from film20.showtimes.models import ScreeningCheckIn
        return self.check_in(user, ScreeningCheckIn.CANCELED)

    @classmethod
    def get_film_to_rate_ids(cls, user, min_num, tag=None):
        exclude = set()
        exclude.update(cls._rated_film_ids(user))
        exclude.update(cls._marked_film_ids(user))
        exclude.update(cls._recently_seen_film_ids(user))
        
        key = cache.Key("to_rate_films", user, tag)
        try:
            to_rate, basket_offs = cache.get(key)
            to_rate.difference_update(exclude)
            if len(to_rate) >= min_num:
                return to_rate
        except TypeError: # cache miss
            to_rate = set()
            basket_offs = 0

        all_ids = cls._to_rate_all_ids(user, tag=tag)

        to_rate.update(cls._long_ago_seen_film_ids(user, tag=tag))

        offset = basket_offs
        while True:
            if not tag:
                basket_size = settings.RATING_BASKET_SIZE
            else:
                basket_size = settings.RATING_TAG_BASKET_SIZE
            ids = all_ids[offset:offset+basket_size]
            if ids:
                offset = offset + basket_size
            to_rate.update(ids)
            to_rate.difference_update(exclude)
            if len(to_rate) >= min_num or not ids:
                break
        
        if offset != basket_offs:
            cache.set(key, (to_rate, offset))
        return to_rate
    
    @classmethod
    def get_next_film_to_rate(cls, user, tag=''):
        films = cls.get_films_to_rate(user, 1, tag)
        return films and films[0] or None

    @classmethod
    def get_films_to_rate(cls, user, n_films, tag=''):
        ids = list(cls.get_film_to_rate_ids(user, n_films, tag))
        films = list(Film.objects.filter(id__in=ids[:n_films]).select_related())
        random.shuffle(films)
        return films

    @classmethod
    def _rated_film_ids(cls, user):
        return set(Rating.get_user_ratings(user).keys())

    @classmethod
    def _long_ago_seen_film_ids(cls, user, tag=''):
        if not user.id:
            return set()
        
        key = cache.Key("long_ago_seen_film_ids", user, tag)
        ids = cache.get(key)
        up_to = datetime.datetime.now() - \
                datetime.timedelta(days=settings.RATING_SEEN_DAYS)
        if ids is None:
            r = Rating.objects.filter(
                user=user, 
                type=Rating.TYPE_FILM, 
                rating__isnull=True,
                last_displayed__lte=up_to,
            )
            if tag:
                r = r.filter(film__objectlocalized__tagged_items__tag__name=tag)
            ids = set(r.values_list('film_id', flat=True))
            cache.set(key, ids)
        return ids

    def seen_by_user(self, user):
        since = datetime.datetime.now() - \
                datetime.timedelta(days=settings.RATING_SEEN_DAYS)
        ratings = Rating.objects.filter(user=user, film=self,
                last_displayed__gt=since)
        return ratings.count()

    def is_rated_by_user(self, user):
        return user.is_authenticated() and self.id in Rating.get_user_ratings(user)

    @classmethod
    def get_user_seen_films(cls, user):
        seen_films = set()
        seen_films.update(cls._recently_seen_film_ids(user))
        seen_films.difference_update(cls._long_ago_seen_film_ids(user))
        seen_films.update(cls._rated_film_ids(user))
        seen_films.update(cls._marked_film_ids(user))
        return seen_films

    @classmethod
    def filter_seen_by_user(cls, user, films):
        seen_films = cls.get_user_seen_films(user)
        films = set(films)
        films.difference_update(seen_films)
        return films

    @classmethod
    def _recently_seen_film_ids(cls, user):
        key = cache.Key("recently_seen_film_ids", user)
        ids = cache.get(key)
        since = datetime.datetime.now() - \
                datetime.timedelta(days=settings.RATING_SEEN_DAYS)
        if ids is None:
            ids = set(Rating.objects.filter(
                user=user, 
                type=Rating.TYPE_FILM, 
                rating__isnull=True,
                last_displayed__gt=since,
            ).values_list('film_id', flat=True))
            cache.set(key, ids)
        return ids

    @classmethod
    def _marked_film_ids(cls, user):
        if not user.id:
            return set()
        from film20.filmbasket.models import BasketItem
        return set(BasketItem.user_basket(user).keys())

    def mark_as_seen(self, user):
        self.mark_films_as_seen(user, [self.id])
    
    @classmethod
    def mark_films_as_seen(cls, user, film_ids):
        last_seen = cls._recently_seen_film_ids(user)
        new = set(film_ids) - last_seen
        last_seen.update(film_ids)
        if user.id and new:
            defer(Rating.mark_films_as_seen, user.id, list(new))
        cache.set(cache.Key("recently_seen_film_ids", user), last_seen)

    def rate(self, user, value, type=1):
        return Rating.rate(user, value, film_id=self.id, type=1)

    @classmethod
    def update_ranking(cls, films):
        ids = [f.id for f in films]
        ranking = dict((r.film_id, (r.average_score, r.number_of_votes)) 
                for r in FilmRanking.objects.filter(film__in=ids, type=1))
    
        for f in films:
            r = ranking.get(f.id)
            f._average_score = r and r[0]
            f._number_of_votes = r and r[1]
        
        return films

    @classmethod
    def create_from_film_on_channel(cls, film_on_channel):
        film = film_on_channel.film or cls(
            title=film_on_channel.title,
            permalink="unmatched-film-%d" % film_on_channel.pk,
            image=None,
            production_country_list='',
            hires_image=None,
        )

        film._film_on_channel = film_on_channel
        film._directors = film_on_channel.directors
        film.on_wishlist = film_on_channel._on_wishlist
        film.on_shitlist = film_on_channel._on_shitlist
        film.guess_rating = film_on_channel._guess_rating
        film._average_score = film_on_channel._average_score
        return film

    @property
    @memoize_method
    def channels(self):
        if not hasattr(self, "_screening_set"):
            return ()
        return self._screening_set.get_channels(self.id or self.title)

    def set_screening_set(self, ss):
        self._screening_set = ss

    @property
    @memoize_method
    def screenings(self):
        c = self.channels
        return c and c[0].screenings or ()

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kw ):
        # delete cache if film was modified
        if not created:
            cache.delete_cache( cache.CACHE_FILM, instance.permalink )
        
        instance.create_thumbnails()
        if created:
            FilmRanking.objects.create(film=instance, type=1, average_score=0, number_of_votes=0)

post_save.connect( Film.post_save, sender=Film)

class ResourceManager( models.Manager ):
    
    def get_query_set( self ):
        return super( ResourceManager, self ).get_query_set().filter( Q( LANG__isnull=True ) | Q( LANG=LANGUAGE_CODE ) )

    def clear_cache( self, object ):
        cache.delete( self.get_cache_key( object ) )

from film20.userprofile.countries import CountryField

class FilmCountryInfo(models.Model, InstanceCache):
    film = models.ForeignKey(Film)
    country_code = CountryField(_('Country'), null=True, blank=True)

    release_date = models.DateField(blank=True, null=True)
    
    class Meta:
        unique_together = (
            ( 'film', 'country_code' ),
        )
    
    def clean_instance_cache_kwargs(self):
        return dict(film_id=self.film_id, country_code=self.country_code),

class PosterManager( ResourceManager ):
    def get_cache_key( self, object ):
        return cache.Key( "object_poster", object.__module__, object.__class__.__name__, object.pk )

    def get_poster( self, object ):
        try:
            return self.get_query_set().get( object=object, is_main=True, LANG=LANGUAGE_CODE )
        except Poster.DoesNotExist:
            try:
                return self.get_query_set().get( object=object, is_main=True, LANG__isnull=True )
            except Poster.DoesNotExist:
                pass
        return None

    def get_image( self, object ):
        key = self.get_cache_key( object )
        poster = cache.get( key )
        if poster is None:
            poster = self.get_poster( object )
            poster = poster.image if poster else None
            cache.set( key, poster )
        return poster


class TrailerManager( ResourceManager ):
    def get_for_object( self, object ):
        return self.get_query_set().filter( object=object, moderation_status=ModeratedObject.STATUS_ACCEPTED ).order_by( '-is_main', 'LANG' )


class Resource( models.Model ):
    object = models.ForeignKey( Object )

    is_main = models.BooleanField( default=False )
    LANG = models.CharField( max_length=2, blank=True, null=True )

    added_by  = models.ForeignKey( User, blank=True, null=True )
    date_added = models.DateTimeField( blank=True, null=True, auto_now_add=True )

    all_objects = models.Manager()

    @property
    def user( self ):
        return self.added_by

    @property
    def person( self ):
        return getattr( self.object, 'person', None )

    @property
    def film( self ):
        return getattr( self.object, 'film', None )

    def get_object_url( self ):
        if self.film:
            return self.film.get_absolute_path()
        return reverse( 'show_person', args=( self.person.permalink, ) )

    class Meta:
        abstract = True

    def save( self, *args, **kwargs ):
        if self.LANG == '': 
            self.LANG = None

        if self.is_main:
            main = self.__class__.objects.filter( object=self.object, is_main=True )
            if self.LANG is not None:
                main = main.filter( LANG=self.LANG )

            if self.pk:
                main = main.exclude( pk=self.pk )

            for p in main:
                p.is_main = False
                p.save()

        elif self.__class__.objects.filter( object=self.object, is_main=True ).count() == 0:
            self.is_main = True

        super( Resource, self ).save( *args, **kwargs )


class Poster( Resource ):
    image = models.ImageField(upload_to=image_path('img/obj'), null=True, blank=True, max_length=256)

    objects = PosterManager()

    class Meta:
        unique_together = (
            ( 'object', 'image' ),
        )

    @classmethod
    def clear_cache( cls, sender, instance, *args, **kwargs ):
        try:
            cls.objects.clear_cache( instance.object )
        except Object.DoesNotExist:
            pass # object already deleted


class Trailer( Resource, ModeratedObject ):
    url = models.URLField( _( 'url' ), max_length=2048, verify_exists=False )
    thumb = models.CharField( _( 'thumbnail url' ), max_length=150, blank=True, null=True )
    duration = models.IntegerField(null=True, blank=True) 
    
    objects = TrailerManager()

    class Meta:
        unique_together = (
            ( 'object', 'url', 'LANG' ),
        )

    def unique_error_message( self, model_class, unique_check ):
        if model_class == type( self ) and unique_check == ( 'object', 'url' ):
            return _( "This film already has the same trailer" )
        return super( Trailer, self ).unique_error_message( model_class, unique_check )

    def save_activity( self ):
        from film20.useractivity.models import UserActivity
        film = self.object.film
        defaults = dict(
            user = self.added_by,
            username = self.added_by.username,
            url = self.url,
            video_thumb = self.thumb,
            film = film,
            film_title = film.get_title(),
            film_permalink = film.permalink,
            url_kind = UserActivity.TRAILER,
            activity_type = UserActivity.TYPE_TRAILER,
            permalink = self.url,
            LANG = self.LANG or LANGUAGE_CODE
        )
        act, created = UserActivity.objects.get_or_create( trailer=self, defaults=defaults)
        if not created:
            for (k, v) in defaults.items():
                setattr(act, k, v)
            act.save()

    def accept( self, user, **kwargs ):
        language = kwargs.get( 'language', None )
        if language is not None:
            self.LANG = None if language[0] == 'all' else language[0]
            self.is_main = kwargs.get( 'is_main', None ) is not None
        super( Trailer, self ).accept( user, **kwargs )

    def save( self, *args, **kwargs ):
        if not self.thumb or not self.duration:
            self.fetch_metadata()
            if self.is_main and self.duration:
                film = self.object.film
                if any(t.strip() in settings.SHORT_FILM_TAGS for t in film.get_tags().split(',')):
                    film.length = (self.duration + 59) / 60
                    film.save()

        skip_activity = kwargs.pop( 'skip_activity', False )
        super( Trailer, self ).save( *args, **kwargs )
        if self.moderation_status == Trailer.STATUS_ACCEPTED and not skip_activity:
            self.save_activity()

    def fetch_metadata( self ):
        from film20.utils.videometa import VideoMeta
        try:
            meta = VideoMeta.fetch(self.url)
            self.thumb = meta.thumbnail
            self.duration = meta.duration
        except Exception, e:
            logger.error('Oops, cannot fetch video meta for %r: %s', self.url, e)

        # TODO: oembed

    @classmethod
    def clear_cache( cls, sender, instance, *args, **kwargs ):
        cls.objects.clear_cache( instance.object )


class TrailerToRemove( ModeratedObject ):
    
    user    = models.ForeignKey( User )
    trailer = models.ForeignKey( Trailer, related_name="remove_link" )

    class Meta:
       verbose_name = _( "Trailer to remove" )
       verbose_name_plural = _( "Trailer to remove" )

    def accept( self, user, **kwargs ):
        super( TrailerToRemove, self ).accept( user, **kwargs )
        
        self.send_notification()
        self.trailer.delete()

    def reject( self, user, reason=None ):
        super( TrailerToRemove, self ).reject( user, reason )

        self.send_notification();

    def send_notification( self ):
        try:
            from film20.notification import models as notification
        except ImportError:
            notification = None

        if self.user != self.moderation_status_by and notification:
            notification.send( [ self.user ], "trailer_to_remove_moderated", { "item": self } )


try:
    moderated_item = ModeratedObjectItem( 
            Trailer, "externallink.can_add_link",
            name="trailer", 
            item_template_name="moderation/trailer/record.html",
            rss_template_name="moderation/trailer/rss.xml"
        )

    moderated_trailer_to_remove = ModeratedObjectItem( 
        TrailerToRemove, "externallink.can_add_link",
        name="trailer-tr", 
        item_template_name="moderation/trailer-tr/record.html",
        rss_template_name="moderation/trailer-tr/rss.xml"
    )

    registry.register( moderated_item )
    registry.register( moderated_trailer_to_remove )
except AlreadyRegistered:
    pass


post_save.connect( Poster.clear_cache, sender=Poster )
post_delete.connect( Poster.clear_cache, sender=Poster )


class PosterAdmin( admin.ModelAdmin ):
    list_display = ( 'object' , 'image', 'added_by', 'date_added', 'is_main' )
    raw_id_fields = ( 'object', 'added_by' )

class TrailerAdmin( admin.ModelAdmin ):
    list_display = ( 'object' , 'url', 'added_by', 'date_added', 'is_main' )
    raw_id_fields = ( 'object', 'added_by' )


class SimilarFilm( models.Model ):
    film_a = models.ForeignKey( Film, related_name='similar_film_a' )
    film_b = models.ForeignKey( Film, related_name='similar_film_b' )
    votes = models.ManyToManyField( User, blank=True, null=True )
    number_of_votes = models.IntegerField( default=0 )
    
    class Meta:
        ordering = ( '-number_of_votes', )
        unique_together = ( 'film_a', 'film_b' )
    
    @classmethod
    def get_similar( cls, film ):
        return cls.objects.filter( film_a=film )

    @classmethod
    def user_votes( cls, film, user ):
        return [ sf.film_b for sf in cls.objects.filter( film_a=film, votes=user ) ]

    @classmethod
    def update_votes( cls, instance ):
        instance.number_of_votes = instance.votes.count()
        if instance.number_of_votes == 0:
            instance.delete()
        else:
            instance.save()

    @classmethod
    def add_vote( cls, user, film_a, film_b ):
        sf, created = SimilarFilm.objects.get_or_create( film_a=film_a, film_b=film_b )
        sf.votes.add( user )
        cls.update_votes( sf )

        sf, created = SimilarFilm.objects.get_or_create( film_a=film_b, film_b=film_a )
        sf.votes.add( user )
        cls.update_votes( sf )

    @classmethod
    def remove_vote( cls, user, film_a, film_b=None ):
        sfs = SimilarFilm.objects.filter( film_a=film_a, votes=user )
        if film_b is not None:
            sfs = sfs.filter( film_b=film_b )
        for sf in sfs:
            sf.votes.remove( user )
            cls.update_votes( sf )

        sfs = SimilarFilm.objects.filter( film_b=film_a, votes=user )
        if film_b is not None:
            sfs = sfs.filter( film_a=film_b )
        for sf in sfs:
            sf.votes.remove( user )
            cls.update_votes( sf )

class FilmCountryInfoInline(admin.TabularInline):
    model = FilmCountryInfo
    extra = 1

class FilmAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_year' , 'tmdb_import_status', 'import_comment')
    search_fields = ('title',)
    raw_id_fields = ['directors', 'writers']
    
    inlines = [
        FilmCountryInfoInline
    ]

from film20.tagging.models import TaggedItem
from django.contrib.contenttypes import generic


class ObjectLocalized(models.Model):
    
    parent = models.ForeignKey(Object)
    tag_list = models.CharField(max_length=255)
    
    objects = QuerySet.as_manager()

    def save(self, *args, **kwargs):
        tag_translated = kwargs.pop( 'tag_translated', False )

        super(ObjectLocalized, self).save(*args, **kwargs)
        logger.debug("saving tags:" +  self.tag_list)
        self.tags = self.tag_list
        self.parent.set_localized_object( self, self.LANG )

        # translate tags
        if not tag_translated:
            logger.debug( "staring translation: <%s|%s>, %s" % ( self.parent, self.LANG, self.tags ) ) 
            from film20.tagging.models import TagTranslation
            
            # get other language
            to_lang = TagTranslation.to_lang( self.LANG )
            try:
                object_localized = ObjectLocalized.objects.get( parent=self.parent, LANG=to_lang )
                current_tags = [ t.name for t in object_localized.tags ]
            except ObjectLocalized.DoesNotExist:
                object_localized = None
                current_tags = []
            
            logger.debug( 'translating %s tags, current: %s' % ( to_lang, current_tags ) )

            tags = [ t for t in current_tags ]
            for tag in self.tags:
                translated = TagTranslation.translate( tag.name, from_lang=self.LANG, to_lang=to_lang )
                logger.debug( 'translation for tag: %s = %s' % ( tag, translated ) )
                if translated is not None:
                    if not translated in tags:
                        tags.append( translated )
            
            if current_tags <> tags:
                if object_localized is None:
                    object_localized = ObjectLocalized.objects.create( parent=self.parent, LANG=to_lang )
                logger.debug( 'saving translated %s tags: %s' % ( to_lang, tags ) )
                object_localized.tag_list = ','.join( tags )
                object_localized.save( tag_translated=True )
        else:
            logger.debug( 'skiping tag translation ...' )
        
    #def save_searchkeys(self, text):
    #    self.searchkey_set.all().delete()
    #    create_searchkeys(text, self.searchkey_set)
            
    def _get_tags(self):
        logger.debug("_get_tags")
        return Tag.objects.get_for_object(self)

    def _set_tags(self, tag_list):
        logger.debug("_set_tags" +  tag_list)
        Tag.objects.update_tags(self, tag_list)
        self.tag_list = ', '.join( [ tag.name for tag in self._get_tags() ] )
        
    def get_tags_as_string(self):
        return ', '.join(t.name for t in self.tags)
    
    def __unicode__( self ):
        return "%s (%s)" % ( self.parent, self.LANG )

    tags = property(_get_tags, _set_tags)
    
    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    
    tagged_items = generic.GenericRelation(TaggedItem,
                                   content_type_field='content_type',
                                   object_id_field='object_id')

class ObjectLocalizedAdmin(admin.ModelAdmin):
    pass

#
#class SearchKey(models.Model):
#    object = models.ForeignKey(Object, blank=False, null=False)
#    object_localized = models.ForeignKey(ObjectLocalized, blank=True, null=True)
#    #object_type = models.IntegerField(choices=Object.OBJECT_TYPE_CHOICES)
#    key_normalized = models.CharField(max_length=128, blank=True, null=True)
#    key_root = models.CharField(max_length=128, blank=True, null=True)        
#    key_letters = models.CharField(max_length=128, blank=False, null=False)
#    text_length = models.IntegerField()
#    
#    def save(self, force_insert=False, force_update=False, *args, **kwargs):
#        if not self.object_localized == None:
#           self.object = self.object_localized.parent
#        #self.object_type = self.object.type
#        super(SearchKey, self).save(*args, **kwargs)
#               
#    def __unicode__(self):
#        return "%s" % self.key_normalized
#        
#def create_searchkeys(text, set):
#    words = get_normalized_word_list(text)
#    roots = get_words_roots(words)
#    letters = get_words_letters(words)
#    for i in range(0, len(words)):
#        key = u' '.join(words[i:])
#        set.create(key_normalized = u' '.join(words[i:]), 
#            key_root = u''.join(roots[i:]), 
#            key_letters=u' '.join(letters[i:]),
#            text_length=len(text)
#        )



class FilmLocalized(ObjectLocalized):
    object_localized = models.OneToOneField(ObjectLocalized, parent_link=True)
    film = models.ForeignKey(Film)
    
    title = models.CharField(max_length=128)
    title_normalized = models.CharField(max_length=128)
    #title_root = models.CharField(max_length=128)
    description = models.CharField(max_length=15000, blank=True, null=True)

    DESC_DISTRIBUTOR = 1
    DESC_USER = 2
    DESCRIPTION_TYPE_CHOICES = (
        (DESC_DISTRIBUTOR, 'Dist'),
        (DESC_USER, 'User'),
    )
    
    # added for FLM-266 
    fetched_description = models.CharField(max_length=15000, blank=True, null=True)
    fetched_description_url = models.CharField(max_length=200, blank=True, null=True)
    fetched_description_url_text = models.CharField(max_length=200, blank=True, null=True)
    fetched_description_type = models.IntegerField(choices=DESCRIPTION_TYPE_CHOICES, blank=True, null=True)
    
    release_year = models.IntegerField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)    
    
    objects = QuerySet.as_manager()
        
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.title_normalized = normalized_text(self.title)
        #self.title_root = string_root_normalized(self.title_normalized)
        super(FilmLocalized, self).save(*args, **kwargs)
        #super(FilmLocalized, self).save_searchkeys(self.title)
        cache.delete(cache.Key("film_localized_film", self.film_id, LANGUAGE_CODE))

    def __unicode__(self):
        return self.title

class FilmLocalizedAdmin(admin.ModelAdmin):
    verbose_name = _('Film localized')
    verbose_name_plural = _('Films localized')
    raw_id_fields = ['film', ]
    search_fields = ('title',)


class ModeratedFilmLocalized( ModeratedObject ):
    LANG = models.CharField( max_length=2, default=LANGUAGE_CODE )
    film = models.ForeignKey( Film )
    user = models.ForeignKey( User )

    title = models.CharField( max_length=128 )
    tag_list = models.CharField( max_length=255 )
    description = models.CharField( max_length=15000, blank=True, null=True )

    objects = LangQuerySet.as_manager()

    class Meta:
        verbose_name = _( "Localized Film" )
        verbose_name_plural = _( "Localized Films" )
        permissions = (
            ( "can_accept_localized_data", "Can accept localized data"),
        )

    def get_old_and_new( self ):
        if self.title:
            old = self.film.get_localized_title()
            new = self.title
        
        elif self.description:
            old = self.film.get_description()
            new = self.description

        elif self.tag_list:
            old = ','.join( filter( bool, ( t.strip() for t in self.film.get_tags().split( ',' ) ) ) )
            new = self.tag_list

        else:
            old = new = ''

        return old, new

    def html_diff( self ):
        old, new = self.get_old_and_new()
        return html_diff( old, new )

    def save( self, **kwargs ):
        super( ModeratedFilmLocalized, self ).save( **kwargs )
        if self.moderation_status == ModeratedFilmLocalized.STATUS_ACCEPTED:
            if self.title:
                self.film.save_localized_title( self.title )

            if self.description:
                self.film.save_description( self.description )

            if self.tag_list:
                self.film.save_tags( self.tag_list )

try:
    moderated_item = ModeratedObjectItem( 
            ModeratedFilmLocalized, "core.can_accept_localized_data",
            name="filmlocalized", 
            item_template_name="moderation/filmlocalized/record.html",
            rss_template_name="moderation/filmlocalized/rss.xml"
        )

    registry.register( moderated_item )
except AlreadyRegistered:
    pass

class PersonLocalized(ObjectLocalized):
    object_localized = models.OneToOneField(ObjectLocalized, parent_link=True)
    person = models.ForeignKey(Person)
    
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    biography = models.TextField( blank=True, null=True )
    
    objects = QuerySet.as_manager()
        
    def save(self, force_insert=False, force_update=False, *args, **kwargs):    
        super(PersonLocalized, self).save(*args, **kwargs)        
        #super(PersonLocalized, self).save_searchkeys(concatenate_words([self.name, self.surname]))
        cache.delete_cache(cache.CACHE_PERSON_LOCALIZED, self.person.id)
        
    def __unicode__(self):
        return concatenate_words([self.name, self.surname])


class ModeratedPersonLocalized( ModeratedObject ):
    LANG = models.CharField( max_length=2, default=LANGUAGE_CODE )
    person = models.ForeignKey( Person )
    user = models.ForeignKey( User )

    name = models.CharField( max_length=50, null=True, blank=True )
    surname = models.CharField( max_length=50, null=True, blank=True )
    biography = models.TextField( blank=True, null=True )

    objects = LangQuerySet.as_manager()

    class Meta:
        verbose_name = _( "Localized Person" )
        verbose_name_plural = _( "Localized Person" )

    def get_old_and_new( self ):
        if self.name or self.surname:
            old = '%s %s' % ( self.person.localized_name, self.person.localized_surname )
            new = '%s %s' % ( self.name, self.surname )
        
        elif self.biography:
            old = self.person.biography
            new = self.biography

        else:
            old = new = ''

        return old, new

    def html_diff( self ):
        old, new = self.get_old_and_new()
        return html_diff( old, new )

    def save( self, **kwargs ):
        super( ModeratedPersonLocalized, self ).save( **kwargs )
        if self.moderation_status == ModeratedPersonLocalized.STATUS_ACCEPTED:
            if self.name or self.surname:
                self.person.localized_name = self.name
                self.person.localized_surname = self.surname

            if self.biography:
                self.person.biography = self.biography

try:
    moderated_item = ModeratedObjectItem( 
            ModeratedPersonLocalized, "core.can_accept_localized_data",
            name="personlocalized", 
            item_template_name="moderation/personlocalized/record.html",
            rss_template_name="moderation/personlocalized/rss.xml"
        )

    registry.register( moderated_item )
except AlreadyRegistered:
    pass


class PersonLocalizedAdmin(admin.ModelAdmin):
    verbose_name = _('Person localized')
    verbose_name_plural = _('People localized')
    raw_id_fields = ['film', ]
    search_fields = ('name','surname',)

def get_character_image_path(instance, filename):
    return 'img/characters/%s/%s' % (filename[0], filename)

class CharacterQuerySet(QuerySet):
    def fetch_related(self):
        def _fetch(items, **kw):
            items = list(items)
            localized = PersonLocalized.objects.filter(person__in=[c.person_id for c in items])
            localized = dict((p.person_id, p) for p in localized)
            for c in items:
                c.person.set_localized_person(localized.get(c.person_id))
                yield c
            
        return self.select_related().postprocess(_fetch)

class Character(models.Model):
    person = models.ForeignKey(Person)
    film = models.ForeignKey(Film)
    """
     Lower number - more important role!
    """
    importance = models.IntegerField(blank=True, null=True)
    character = models.CharField(max_length=255, blank=True, null=True)

    description_lead = models.CharField(max_length=350, blank=True, null=True)
    description_full = models.CharField(max_length=1000, blank=True, null=True)

    image = models.ImageField(upload_to=get_character_image_path, null=True, blank=True)
    image_thumb = models.ImageField(upload_to=get_character_image_path, null=True, blank=True)
    image_thumb_lost = models.ImageField(upload_to=get_character_image_path, null=True, blank=True)
    
    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    objects = CharacterQuerySet.as_manager()

    def __unicode__(self): 
        return unicode(self.character)

from django import forms
class CharacterModelForm( forms.ModelForm ):
    description_lead = forms.CharField( widget=forms.Textarea, required=False )
    description_full = forms.CharField( widget=forms.Textarea, required=False )
    class Meta:
        model = Character

class CharacterAdmin(admin.ModelAdmin):
    list_display = ('character', 'film', 'person', 'LANG', )
    raw_id_fields = ['film', 'person', ] 
    search_fields = ('character', 'film__title', 'person__name', 'person__surname',)
    form = CharacterModelForm

class RatingOutOtBoundException(Exception):
    """
       Exception thrown when someone tries allocating a rating
       that is not in range 1..10
    """
    pass

class RatingQuerySet(QuerySet):
    def similar_ratings(self, user):
        return self.filter(user__main_users__compared_user=user)\
                   .order_by('user__main_users__score')
    
    def film(self, film):
        return self.filter(rating__isnull=False, type=1, film=film.id)

class Rating(FieldChangeDetectorMixin, models.Model):
    DETECT_CHANGE_FIELDS = ('rating', )

    objects = RatingQuerySet.as_manager()
    
    # parent object rated, 
    # in case of rating a film, it's always the film's parent object ID
    # (no matter if it's about rating an actor in the film, a film extra feature and so on)
    # in case of rating a person (in general, not in a particular film), it's the person's 
    # parent object ID 
    parent = models.ForeignKey(Object)
    
    # rating user
    user = models.ForeignKey(User)
    
    # film rated
    film = models.ForeignKey(Film, blank=True, null=True, related_name="film_ratings")
    # person rated (general or in film)
    actor = models.ForeignKey(Person, blank=True, null=True, related_name="rated_as_actor", verbose_name="person acting like actor")
    director = models.ForeignKey(Person, blank=True, null=True, related_name="rated_as_director", verbose_name="person acting like director")
    
    # rating given by user
    rating = models.IntegerField(blank=True, null=True)
    # normalized rating
    normalized = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    
    # guess rating basing on algorithm 1
    guess_rating_alg1 = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    # guess rating basing on algorithm 2
    guess_rating_alg2 = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    
    # rating types
    TYPE_FILM = 1
    TYPE_DIRECTOR = 2
    TYPE_ACTOR = 3
    TYPE_ACTOR_IN_FILM = 4
    TYPE_DIRECTOR_IN_FILM = 5
    
    TYPE_EXTRA_SCREENPLAY = 6  
    TYPE_EXTRA_SPECIAL_EFFECTS = 7
    TYPE_EXTRA_EDITING = 8
    TYPE_EXTRA_MUSIC = 9
    TYPE_EXTRA_CAMERA = 10
    
    TYPE_EXTRA_NOVELTY = 11
    TYPE_EXTRA_BRUTALITY = 12
    TYPE_EXTRA_SEXUALITY = 13    
    TYPE_EXTRA_DIRECTORY = 14
    TYPE_EXTRA_ACTING = 15

    TYPE_MOST_RIDICULOUS_TRANSLATION = 50
    TYPE_DIALOGUES = 51
    
    # rating types groups
    ADVANCED_RATING_TYPES = [
        TYPE_EXTRA_DIRECTORY,
        TYPE_EXTRA_SCREENPLAY,
        TYPE_EXTRA_ACTING,
        TYPE_EXTRA_SPECIAL_EFFECTS,
        TYPE_EXTRA_EDITING,
        TYPE_EXTRA_MUSIC,
        TYPE_EXTRA_CAMERA,
        TYPE_EXTRA_NOVELTY,
    ]

    EXTRA_TYPES = [
        TYPE_EXTRA_NOVELTY,
        TYPE_ACTOR_IN_FILM,
        TYPE_EXTRA_ACTING,
        TYPE_MOST_RIDICULOUS_TRANSLATION,
    ]

    OSCAR_TYPES = [
        TYPE_EXTRA_DIRECTORY,
        TYPE_EXTRA_SCREENPLAY,
        TYPE_EXTRA_SPECIAL_EFFECTS,
        TYPE_EXTRA_EDITING,
        TYPE_EXTRA_MUSIC,
        TYPE_EXTRA_CAMERA,
    ]
    
    RATING_TYPES = [
        TYPE_FILM,
        TYPE_ACTOR,         
        TYPE_DIRECTOR,
    ]
    RATING_TYPES += OSCAR_TYPES
    RATING_TYPES += EXTRA_TYPES
    
    ALL_RATING_TYPES = (
        (TYPE_FILM, _('Film'),),
        (TYPE_DIRECTOR, _('Director'),),
        (TYPE_ACTOR, _('Actor'),),
        (TYPE_ACTOR_IN_FILM, _('Actor in film'),),
        (TYPE_DIRECTOR_IN_FILM, _('Director in film'),),        
        (TYPE_EXTRA_SCREENPLAY, _('Screenplay'),),
        (TYPE_EXTRA_SPECIAL_EFFECTS, _('Special effects'), ),
        (TYPE_EXTRA_EDITING, _('Editing'), ),
        (TYPE_EXTRA_MUSIC, _('Music'), ),
        (TYPE_EXTRA_CAMERA, _('Camera'), ),
        (TYPE_EXTRA_NOVELTY, _('Novelty'), ),
        (TYPE_EXTRA_BRUTALITY, _('Brutality'), ),
        (TYPE_EXTRA_SEXUALITY, _('Sexuality'), ),        
        (TYPE_EXTRA_DIRECTORY, _('Directory'), ),
        (TYPE_EXTRA_ACTING, _('Acting'), ),
    )
    
    INDEX_ID = 0
    INDEX_LABEL = 1
    
    # rating type
    type = models.IntegerField(choices=ALL_RATING_TYPES)

    MIN_COMMON_VOTES = 5

    # number of ratings of users with common taste
    number_of_ratings = models.IntegerField(blank=True, null=True)

    # the date when the object was last displayed to be rated (makes sens for TYPE_FILM only)
    last_displayed = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    
    # the date when the object was first rated
    first_rated = models.DateTimeField(blank=True, null=True)
    # the date when rating was last rated
    last_rated = models.DateTimeField(blank=True, null=True)

    number_of_comments = models.IntegerField(null=True, blank=True)
        
    def __init__(self, *args, **kw):
        # rating importer sets this to False to prevent notification spamming
        self._send_notice = kw.pop('_send_notice', True)
        self._skip_activity = kw.pop('_skip_activity', False)
        return super(Rating, self).__init__(*args, **kw)

    @classmethod
    def rate(cls, user, value, film_id=None, actor_id=None, director_id=None, type=1, overwrite=True, _send_notice=True, _skip_activity=False):
        if not user.id:
            # temporary anonymouse user, store to db on first rating
            user.store_to_db()
        extra = cls._extra_lookup(
                film_id=film_id,
                actor_id=actor_id,
                director_id=director_id)

        parent_id = film_id or actor_id or director_id

        r, created = Rating.objects.get_or_create(
                parent_id=parent_id,
                user=user,
                type=type,
                defaults={'rating': value, '_send_notice': _send_notice, '_skip_activity': _skip_activity},
                **extra
        )
        exists = not created
        if not created and overwrite:
            r.rating = value
            r._send_notice = _send_notice
            r._skip_activity = _skip_activity
            r.save()
        return exists

    @classmethod
    def get_ratings(cls, film_id=None, actor_id=None, director_id=None, type=1):
        extra = cls._extra_lookup(
                    film=film_id,
                    actor=actor_id,
                    director=director_id
        )
        ratings = Rating.objects.filter(
                rating__isnull=False,
                type=type,
                **extra
        )
        return dict(ratings.values_list('user_id', 'rating'))

    @classmethod
    def get_rating(cls, user, film_id=None, actor_id=None, director_id=None, type=1):
        extra = cls._extra_lookup(
                    film=film_id,
                    actor=actor_id,
                    director=director_id
        )
        try:
            r = cls.objects.get(
                    user=user,
                    type=type,
                    **extra
            )
            return r.rating
        except cls.DoesNotExist, e:
            pass

    @classmethod
    def _extra_lookup(cls, **kw):
        extra = {}
        for k, v in kw.items():
            if v:
                extra[k] = int(v)
            else:
                if k.endswith('_id'):
                    k = k[:-3]
                extra[k + "__isnull"] = True
        return extra

    def save(self, *args, **kw):
        self.normalized = self.rating
        # invalidate cache
        self.clear_cache()

        if ( (self.rating >= 1) and (self.rating <= 10) or (self.rating is None) ):
            if self.rating is not None:
                now = datetime.datetime.now()
                self.last_rated = now
                if self.is_field_changed('rating'):
                    self.first_rated = now
            super(Rating, self).save(*args, **kw)
        else:
            raise RatingOutOtBoundException()
        
        if self.has_changed():
            from film20.core.deferred import defer
            if self.type == 1 and not self._skip_activity:
                self.save_activity()
#                defer(self.save_activity)

    def clear_cache( self ):
        if self.type is Rating.TYPE_FILM:
            try:
                cache.delete_cache(cache.CACHE_USER_RATINGS_COUNT, unicode(self.user.id))
                key = cache.Key( "user_ratings", self.user.id )
                ratings = cache.get( key )
                if ratings is not None:
                    if ratings.has_key( self.film.id ):
                        ratings.pop( self.film.id )
                        cache.set( key, ratings )
            except Exception, e: 
                pass

    @classmethod
    def get_user_ratings(cls, user_id):
        if isinstance(user_id, User):
            user_id = user_id.id

        if settings.USE_REDIS:
            from film20.utils import redis_intf
            return redis_intf.get_user_ratings(user_id)

        key = cache.Key("user_ratings", user_id)
        ratings = cache.get(key)
        if ratings is None:
            if user_id:
                ratings = dict(Rating.objects.filter(user=user_id, type=Rating.TYPE_FILM,
                    rating__isnull=False).values_list('film_id', 'rating'))
            else:
                ratings = {}
            cache.set(key, ratings)
        return ratings

    @classmethod
    def get_user_directors_ratings(cls, user_id):
        key = cache.Key("user_directors_ratings", user_id)
        ratings = cache.get(key)
        if ratings is None:
            ratings = Rating.objects.filter(user=user_id, type=Rating.TYPE_FILM,
                    rating__isnull=False).values_list('film__directors', 'rating')
            cache.set(key, ratings)
        return ratings

    @classmethod
    def get_film_ratings(cls, film_id):
        key = cache.Key("film_ratings", film_id)
        ratings = cache.get(key)
        if ratings is None:
            ratings = dict(Rating.objects.filter(film=film_id, type=Rating.TYPE_FILM,
                    rating__isnull=False, actor__isnull=True, director__isnull=True).values_list('user_id', 'rating'))
            cache.set(key, ratings)
        return ratings


    def __unicode__(self):        
        return unicode(self.user.username) + ", " + unicode(self.parent.permalink) + ", " + unicode(self.rating) + " (" + unicode(self.normalized) + ")"
    
    @classmethod
    def count_for_user(cls, user):
        return len(Film._rated_film_ids(user))
    
    @classmethod
    def post_delete( cls, sender, instance, *args, **kwargs ):
        instance.clear_cache()
    
    @classmethod
    def inc_count_for_user(cls, user, value, type=TYPE_FILM):
        key = "rating_cnt_%s_%s" % (user, type)
        try:
            if value > 0:
                cache.incr(key, value)
            else:
                cache.decr(key, -value)
        except ValueError:
            pass
    
    def percent_score(self):
        if hasattr(self, 'score'):
            return int(round((1 - self.score * self.score) * 100))
    
    def has_changed(self):
        return self.is_field_changed('rating')
        
    def get_comment_title(self):
        # TODO - add comment title
        return 'comment title'
    
    def get_absolute_url(self):
        return make_absolute_url(self.get_slug())

    def get_slug(self):
        return reverse('show_rating', args=[unicode(self.user), self.id])

    def get_absolute_url_old_style(self):
        return self.get_absolute_url()

    def get_related_films(self):
        return self.film,

    def get_slug(self):
        return reverse('show_rating', args=[unicode(self.user), self.id])

    @classmethod
    def mark_film_as_seen(cls, user_id, film_id):
        rating, created = cls.objects.get_or_create(
            user_id=user_id,
            type=cls.TYPE_FILM,
            parent_id=film_id,
            actor__isnull=True,
            director__isnull=True,
            defaults=dict(
                film_id=film_id,
            ),
        )
        if not created:
            rating.last_displayed = datetime.datetime.now()
            rating.save()
        return rating

    @classmethod
    def mark_films_as_seen(cls, user_id, film_ids):
        for film_id in film_ids:
            cls.mark_film_as_seen(user_id, film_id)

    @classmethod
    def recompute_user_features(cls, user):
        profile = user.get_profile()
        if profile.recommendations_status in (profile.FAST_RECOMMENDATIONS, ):
            from film20.recommendations import engine
            engine.compute_user_features(user, True)
            cache.delete(cache.Key("tv_user_recommended", user))
            cache.delete(cache.Key("cinema_user_recommended", user))
            cache.delete(cache.Key("popular_films_main_page", user))

    @classmethod
    def grouping_started(cls, sender, instance, *args, **kwargs):
        if instance.activity_type != 4 or instance.related_rating is None:
            return

        if not settings.USE_REDIS:
            eta = datetime.datetime.now() + datetime.timedelta(seconds=settings.RECOMPUTE_USER_FEATURES_TIME_OFFSET)
            defer(cls.recompute_user_features, instance.user, _eta=eta)

    @classmethod
    def grouping_finished( cls, sender, instance, *args, **kwargs ):
        # filter only rating activities
        if instance.activity_type != 4 or  instance.related_rating is None:
            return

        from film20.notification.models import send as send_notice
        from film20.useractivity.models import UserActivity
        from film20.core.urlresolvers import reverse

        _send_notice = instance.related_rating._send_notice

        # need to refresh useractivity
        try:
            instance = UserActivity.objects.get( pk=instance.pk )

            count = instance.hidden_activities
            if count:
                logger.debug("%d extra movies rated", count)

            if count == 0:
                rr = instance.related_rating
                link = rr.film.get_absolute_path()
                reviewed = ShortReview.objects.filter(
                        user=rr.user,
                        object=rr.film,
                        created_at__gte=instance.created_at-datetime.timedelta(minutes=30)).count()
                if reviewed:
                    _send_notice = False
            else:
                link = reverse('ratings', kwargs={'username': unicode(instance.user)}) + '?sort_by=date'

            if _send_notice:
                film = instance.related_rating.film
                send_notice([instance.user], 'useractivity_films_rated', dict(
                    film=film,
                    film_kind=gettext("TV series") if film and film.is_tv_series else gettext("film"),
                    rating=instance.related_rating.rating,
                    extra_cnt=count,
                    link=link,
                    picture=film.get_absolute_image_url(),
                    hashtags=UserActivity.get_hashtags(instance.related_rating.film)
                ))
        except UserActivity.DoesNotExist:
            logger.info( "Activity is removed, sending notification skipped" )

        if not settings.USE_REDIS:
            cls.recompute_user_features(instance.user)

    def save_activity( self ):
        from film20.useractivity.models import UserActivity
        if self.is_field_changed('rating'):
            # update activity if user already rated this film in 5m
            tm = datetime.datetime.now() - datetime.timedelta( seconds=300 )
            activities = UserActivity.all_objects.filter( created_at__gt=tm, user=self.user, film=self.film,
                                                                    LANG=settings.LANGUAGE_CODE, activity_type=UserActivity.TYPE_RATING )
            if len( activities ) > 0:
                act = activities[len( activities ) - 1]
            else:
                act = UserActivity()
                act.content = 0
                act.user = self.user
                act.film = self.film
                act.username = self.user.username
                act.film_title = self.film.get_title()
                act.film_permalink = self.film.permalink
                act.activity_type = UserActivity.TYPE_RATING
                act.permalink = reverse('ratings', kwargs={'username': unicode(self.user)})
            act.status = self.user.is_active and self.rating and UserActivity.PUBLIC_STATUS or UserActivity.INACTIVE_STATUS
            act.related_rating = self
            act.rating = self.rating
            act.save()

from film20.useractivity.signals import grouping_started, grouping_finished
grouping_finished.connect( Rating.grouping_finished, dispatch_uid="rating_grouping_finished_signal" )
grouping_started.connect( Rating.grouping_started, dispatch_uid="rating_grouping_started_signal" )
post_delete.connect( Rating.post_delete, sender=Rating )

class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent', 'rating', 'normalized', 'guess_rating_alg1', 'guess_rating_alg2', 'type', 'last_rated')
    list_filter = ['user', 'last_rated',]
    raw_id_fields = ['actor', 'director', 'film','parent', 'user',]
    # TODO: represent type as select

class FilmRanking(models.Model):
    film = models.ForeignKey(Film)
    actor = models.ForeignKey(Person, null=True)

    objects = QuerySet.as_manager()
    # rating type
    type = models.IntegerField(choices=Rating.ALL_RATING_TYPES)
    
    # average score (computed)
    average_score = models.DecimalField(max_digits=4, decimal_places=2)
    
    number_of_votes = models.IntegerField()

    updated_at = models.DateTimeField(auto_now=True, null=True)
   
    MIN_NUM_VOTES_FILM = getattr(settings, "RANKING_MIN_NUM_VOTES_FILM", 25)
    MIN_NUM_VOTES_OTHER = getattr(settings, "RANKING_MIN_NUM_VOTES_OTHER", 10)
    
class FilmRankingAdmin(admin.ModelAdmin):
    None

class ShortReviewManager(models.Manager):
    
    # overridden method for FLM-707
    def get_query_set(self):
        return super(ShortReviewManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)
    
    def create_for_film(self, user, film, text, rating):
        try:
            r = ShortReview.objects.get(user=user, object=film)
        except ShortReview.DoesNotExist:
            r = ShortReview(user=user, 
                            object=film, 
                            type=ShortReview.TYPE_SHORT_REVIEW)
        r.rating = rating
        r.review_text=text
        r.save()
        return r
            
class ShortReview(Object):
    """
        Short review of any rateable object (film, actor, director),
        to be fetched together with those objects
    """
    parent = models.OneToOneField(Object, parent_link=True)

    # kind
    WALLPOST = 1
    REVIEW = 2

    KIND_CHOICES = (
        (WALLPOST, 'Wall post'),
        (REVIEW, 'Review'),
    )
    
    kind = models.IntegerField(choices=KIND_CHOICES, default=WALLPOST)
    
    # reviewed object
    object = models.ForeignKey(Object, related_name="short_reviews", blank=True, null=True)
    
    # reviewing user
    user = models.ForeignKey(User) 
    
    # associated rating
    rating = models.ForeignKey(Rating, related_name="short_reviews", blank=True, null=True)
    
    # review text
    review_text = models.CharField(max_length=1000)
    
    # the dates
    created_at = models.DateTimeField(_('Created at'))
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    # assign manager    
    objects = ShortReviewManager()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = _('Short review')
        verbose_name_plural = _('Short reviews')

    def __init__(self, *args, **kw):
        self.tags = kw.pop('tags', None)
        super(ShortReview, self).__init__(*args, **kw)

    def get_title(self):
        """
            If wall post is connected with object returns title,
            if not returns None
        """

        the_title = ""
        
        # regular wall post
        if self.object is None:
            return None
        # film wall post
        elif self.object.type == Object.TYPE_FILM:
            the_title += unicode(Film.objects.get(id=self.object_id).get_title())
        # person wall post
        elif self.object.type == Object.TYPE_PERSON:
            person = Person.objects.get(id=self.object_id)
            the_title += unicode(person.name + " " + person.surname)
        # festival wall post
        elif self.object.type == Object.TYPE_FESTIVAL:
            from film20.festivals.models import Festival
            festival = Festival.objects.get(id=self.object_id)
            the_title += unicode(festival.name)
        # other type of wall post (we should not really be here, all types should be handled separately)
        else:            
            return None
        if self.rating is not None:
            if self.rating.rating is not None:
                the_title += " (" + unicode(self.rating.rating) + ")"
        return the_title

    def get_comment_title(self):
        """
            Returns title for comment. If wall post is connected with object retunrs title,
            if not returns None
        """
        return self.get_title()

    def get_absolute_url(self):
        """
            Returns absolute url for wall post
        """
        return make_absolute_url(self.get_slug())

    def get_absolute_url_old_style(self):
        """
        http://jira.filmaster.org/browse/FLM-1185
        """
        if self.kind == ShortReview.REVIEW:
            try:
                # warning: this doesn't work for non-films (not an issue as we don't have old style short reviews of people)
                if self.object.type == Object.TYPE_FILM:
                    permalink = self.object.permalink
                    username = self.user.username
                    return settings.FULL_DOMAIN_OLD + "/" + urls["FILM"] + "/" \
                        + unicode(permalink) +"/" \
                        + urls['SHORT_REVIEW_OLD'] +"-"\
                        + unicode(username) +"/"
                else:
                    return "#ERROR-NOT-A-FILM-REVIEW" # for wall posts of kind WALL_POST

            except Exception, e:
                logger.debug(e)
                return "#ERROR" # for wall posts of kind WALL_POST
        else:
            return "#NOT-SUPPORTED" # for wall posts of kind WALL_POST

    def get_slug(self):
        return reverse('show_wall_post', args=[unicode(self.user), self.id])

#    @transaction.commit_on_success    
    def delete(self):
        """
            Deletes the user activity first
        """
        logger.debug("Trying to delete referenced user activity for short review id: " + str(self.id))
        from film20.useractivity.models import UserActivity
        try:
            ua = UserActivity.all_objects.get(
                film=self.object, 
                user=self.user,
                short_review = self,
                LANG=self.LANG)                    
            ua.delete()
            logger.debug("Deleted referenced user activity for short review id: " + str(self.id))
        except UserActivity.DoesNotExist, e:
            logger.debug(e)
            logger.debug("Failed to delete referenced user activity for short review id: " + str(self.id))

        super(ShortReview, self).delete()
        
#    @transaction.commit_on_success    
    def save(self, *args, **kwargs):
        """
            Save related Rating automatically when saving the review.
            Many reviews (in different languages) of the same object
            may be connected with the same Rating object
            (but in general it will be one to one as most users use
            one locale)
        """
        
        logger.debug(self)
            
        try:
            rating = Rating.objects.get(
                user = self.user,
                parent = self.object,
                type = Rating.TYPE_FILM,                
            )
        except Rating.DoesNotExist:
            rating = None
        self.rating = rating    
        if not self.permalink:
            self.permalink='FIXME'
        if not self.created_at:
            self.created_at = datetime.datetime.today()

        super(ShortReview, self).save()
        if self.tags is not None:
            Tag.objects.update_tags(self, self.tags)
        self.save_activity()

        # delete from cache
        if rating != None:
            cache.delete_cache(cache.CACHE_SHORT_REVIEW_FOR_RATING, self.rating.id)

    def save_activity(self):
        """
            Save new activity, if activity exists updates it
        """
        from film20.useractivity.models import UserActivity
        
        defaults = dict(
            user=self.user,
            username=self.user.username,
            activity_type = UserActivity.TYPE_SHORT_REVIEW,
            short_review = self,
            title = self.get_title(),
            content = self.review_text,
            status = self.status,
            permalink = self.get_absolute_url(),
            rating = None if not self.rating else self.rating.rating, # http://jira.filmaster.org/browse/FLM-1464
            LANG = settings.LANGUAGE_CODE,
        )
        if self.object_id:
            if self.object.type == Object.TYPE_FILM:
                film = Film.objects.select_related().get(id=self.object.id)
                defaults.update(dict(
                    film=film,
                    film_title=film.get_title(),
                    film_permalink=film.permalink,
                ))
            elif self.object.type == Object.TYPE_PERSON:
                person = Person.objects.get(id=self.object_id)
                defaults.update(dict(
                    person=person,
                ))
        
        act, created = UserActivity.all_objects.get_or_create(short_review=self, defaults=defaults)
        if not created:
            for (k, v) in defaults.items():
                setattr(act, k, v)
            act.save()

    def get_related_films(self):
        if self.object and self.object.type == Object.TYPE_FILM:
            return self.object,
        return ()


class ShortReviewAdmin(admin.ModelAdmin):
    list_display = ('object', 'review_text',)
    raw_id_fields = ['parent', 'object', 'user','rating',]


class ShortReviewOld(models.Model):
    """
        Short review of any rateable object (film, actor, director),
        to be fetched together with those objects
    """

    # link to the rating object
    rating = models.ForeignKey(Rating, related_name="short_reviewsold")
    
    # review text
    review_text = models.CharField(max_length=255)
    
    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)    
    
class ShortReviewAdminOld(admin.ModelAdmin):
    list_display = ('rating', 'review_text',)


class RatingComparator(models.Model):

    objects = QuerySet.as_manager()

    main_user = models.ForeignKey(User, related_name="main_users", verbose_name="the main user")
    compared_user = models.ForeignKey(User, related_name="compared_users", verbose_name="the compared user")

    comment = models.CharField(max_length=255)
    score = models.DecimalField(max_digits=4, decimal_places=2)
    score2 = models.DecimalField(max_digits=4, decimal_places=2, default="0.00")
    common_films = models.IntegerField()
    sum_difference = models.IntegerField()
    
    previous_save_date = models.DateTimeField(blank=True, null=True)
    
    # the dates
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)
    
    MIN_COMMON_FILMS = getattr(settings, "MIN_COMMON_FILMS", 5)
    MIN_COMMON_TASTE = getattr(settings, "MIN_COMMON_TASTE", 2.1)  

    def __unicode__(self):
        return unicode(self.main_user) + " vs " + unicode(self.compared_user) + " (" + unicode(self.score) + ")"

class RatingComparatorAdmin(admin.ModelAdmin):
    # TODO: displaying just the score makes no sense, but how to display users?
    list_display = ('score','score2',  'common_films', 'sum_difference', 'previous_save_date', 'updated_at',)
    raw_id_fields = ['main_user', 'compared_user', ] 
    
class FilmComparator(models.Model):
    main_film = models.ForeignKey(Film, related_name="main_films",  verbose_name="the main film")
    compared_film = models.ForeignKey(Film,  related_name="compared_films",  verbose_name="the compared film")
    score = models.DecimalField(max_digits=5,  decimal_places=3,  default="0.000")
    
    MIN_FILM_COMPARATOR_SCORE = getattr(settings,  "MIN_FILM_COMPARATOR_SCORE",  0.2)
    
    def __unicode__(self):
        return unicode(self.main_film) + " vs " + unicode(self.compared_film) + " (" + unicode(self.score) + ")"
        
class FilmComparatorAdmin(admin.ModelAdmin):
    list_display = ('main_film', 'compared_film', 'score', )
    raw_id_fields = ['main_film',  'compared_film', ]
    list_filter = ['main_film']
    
class Recommendation(models.Model):
    # guess rating basing on algorithm 1
    guess_rating_alg1 = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    # guess rating basing on algorithm 2
    guess_rating_alg2 = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    # Foreign key to Film model
    film = models.ForeignKey(Film, blank=True, null=True, related_name="film_recommendation")
    # Foreing key to User model
    user = models.ForeignKey(User)
    
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user',  'film',  'guess_rating_alg1',  'guess_rating_alg2')
    list_filter = ['user',  'film']
    
##### Logging objects #####

class FilmLog(AbstractLog):
    film = models.ForeignKey(Film)
    title = models.CharField(max_length=128)
    release_year = models.IntegerField()
    release_date = models.DateField(blank=True, null=True)
    
    tag_list = models.CharField(max_length=255)
    localized_title = models.CharField(max_length=128)     
    
    def __unicode__(self):
        return unicode(self.title) + " [ " +  unicode(self.version_timestamp) + "]" 

class FilmLogAdmin(admin.ModelAdmin):
    list_display = ('LANG', 'title', 'version_timestamp', 'user', 'type', 'comment')
    list_filter = ['version_timestamp', 'user', 'type']
    raw_id_fields = ['film', 'user', ]
    search_fields = ('title','user__username',) 

class PersonLog(AbstractLog):
    person = models.ForeignKey(Person)
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    day_of_birth = models.IntegerField(blank=True, null=True)
    month_of_birth = models.IntegerField(blank=True, null=True)
    year_of_birth = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    is_director = models.BooleanField();
    is_actor = models.BooleanField();
    is_writer = models.BooleanField()
    # number of ratings
    actor_popularity = models.IntegerField()
    director_popularity = models.IntegerField()
    writer_popularity = models.IntegerField()
    # number of ratings in last month
    actor_popularity_month = models.IntegerField(default=0)
    director_popularity_month = models.IntegerField(default=0)
    writer_popularity_month = models.IntegerField(default=0)
    tag_list = models.CharField(max_length=255)

    def __unicode__(self):
        return unicode(self.name) + " " + unicode(self.surname) + " [ " +  unicode(self.version_timestamp) + "]" 

class PersonLogAdmin(admin.ModelAdmin):
    list_display = ('LANG', 'name', 'surname', 'version_timestamp', 'user', 'type', 'comment')
    list_filter = ['version_timestamp', 'user', 'type']
    raw_id_fields = ['person', 'user', ]
    search_fields = ('name','surname','user__username',)

class DeferredTask(models.Model):
    queue_name = models.CharField(max_length=64)
    data = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    eta = models.DateTimeField(null=True, blank=True)
    try_cnt = models.IntegerField(default=0)
    max_tries = models.IntegerField(default=5)
    
    def __init__(self, *args, **kw):
        if 'eta' not in kw:
            kw['eta'] = datetime.datetime.now()
        super(DeferredTask, self).__init__(*args, **kw)
    
    def run(self):
        from film20.utils.deferred import run, PermanentTaskFailure
        try:
            ret = run(self.data.decode('base64'))
            self.delete()
        except PermanentTaskFailure:
            self.delete()
            logger.debug("permanent task failure")
        except Exception, e:
            logger.exception(e)
            self.try_cnt += 1
            if self.max_tries and self.try_cnt >= self.max_tries:
                self.delete()
                logger.debug("max number of tries reached (%d), stop", self.max_tries)
                return
            self.eta = datetime.datetime.now() + datetime.timedelta(seconds=2**self.try_cnt)
            self.save()
            logger.debug("task will be reexecuted at %s", self.eta)
            
    @classmethod
    def run_all(cls):
        tasks = cls.objects.filter(eta__lte=datetime.datetime.now())
        for task in tasks:
            task.run()
    

USER_RATINGS_NOTICE_IDLE_SECONDS = getattr(settings, 'USER_RATINGS_NOTICE_IDLE_SECONDS', 1800)

class UserRatingTimeRange(models.Model):
    user = models.ForeignKey(User)
    first_rated = models.DateTimeField(null=True)
    last_rated = models.DateTimeField(null=True)
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
        
    def __unicode__(self):
        return u"%s: %s - %s" % (self.user, self.first_rated, self.last_rated)

    @classmethod
    def rating_post_save(cls, sender, instance, *args, **kw):
        if instance.type != 1 or not instance.has_changed():
            return
        range, created = UserRatingTimeRange.objects.get_or_create(
            user=instance.user,
            LANG=LANGUAGE_CODE,
            defaults=dict(
                first_rated=instance.last_rated,
                last_rated = instance.last_rated
            ),
        )
        if not created:
            if not range.first_rated:
                range.first_rated = instance.last_rated
            range.last_rated = instance.last_rated
            range.save()
    
    @classmethod
    def process_rating_timerange(cls, time_delta = USER_RATINGS_NOTICE_IDLE_SECONDS):
        '''
        Gets a list of ratings from last half an hour (default for USER_RATINGS_NOTICE_IDLE_SECONDS)
        and for each rating, tries to get a list of ratings for this user within the same period.
        If successful, it sends a notice (so that the ratings can be propagated to twitter/facebook)
        and creates an activity (so that the ratings appear on user's wall).
        '''
        from film20.useractivity.models import UserActivity
        
        tm = datetime.datetime.now() - datetime.timedelta(seconds=time_delta)

        for m in cls.objects.filter(last_rated__lte=tm, first_rated__isnull=False, LANG=LANGUAGE_CODE):
            # offset is just in case if someone put a lot of ratings using api
            last_ratings = Rating.objects.filter(
                user=m.user,
                last_rated__gte=m.first_rated,
                type=Rating.TYPE_FILM,
                rating__isnull=False,
                film__isnull=False,
                actor__isnull=True,
                director__isnull=True
            ).order_by('-rating')

            cnt = last_ratings.count()
            last_ratings = last_ratings[:1]
            # TODO - move this code to UserActivity pre_save handler
            with transaction.commit_on_success():
                if cnt:
                    # save rating activity
                    cls.save_activity(last_ratings, cnt, m.user)
                    logger.info("%d movies rated", cnt)
                    
                    from film20.notification.models import send as send_notice
                    from film20.core.urlresolvers import reverse
                    if cnt==1:
                        link = last_ratings[0].film.get_absolute_path()
                    else:
                        link = reverse('ratings', kwargs={'username': unicode(m.user)}) + '?sort_by=date'
                    send_notice([m.user], 'useractivity_films_rated', dict(
                        film=last_ratings[0].film,
                        rating=last_ratings[0].rating,
                        extra_cnt=cnt-1,
                        link=link,
                        picture=last_ratings[0].film.get_absolute_image_url(),
                        hashtags=UserActivity.get_hashtags(last_ratings[0].film)
                    ))
                m.first_rated = None
                m.save()

    @classmethod
    def save_activity(self, last_ratings, cnt, user):
        """
            Save rating activity
        """
        from film20.useractivity.models import UserActivity

        act = UserActivity()
        act.user = user
        profile = Profile.objects.get(user=user)
        act.username = user.username
        act.film = last_ratings[0].film
        act.related_rating = last_ratings[0]
        act.rating = last_ratings[0].rating
        act.film_title = last_ratings[0].film.get_title()
        act.film_permalink = last_ratings[0].film.permalink
        act.permalink = reverse('ratings', kwargs={'username': unicode(user)})
        act.content = str(cnt - 1)
        act.activity_type = UserActivity.TYPE_RATING
        act.status = UserActivity.PUBLIC_STATUS
        act.save()
    
MIN_VOTES_USER = getattr(settings, 'RECOMMENDATIONS_MIN_VOTES_USER')

class RecomError(models.Model):
    count = models.IntegerField(default = 0)
    sum = models.DecimalField(max_digits=16, decimal_places=8, default=0)
    date = models.DateField(auto_now_add=True, unique=True)

    def __repr__(self):
        return "<RecomError %s: %.4f>" % (self.date, float(self.sum/self.count)**0.5)

    @classmethod
    def update(cls, user, film_id, rating):
        from film20.recommendations import engine
        guess_rating = engine.compute_guess_score(user, film_id)
        if guess_rating:
            v = Decimal(str((guess_rating - rating) ** 2))
            obj, created = cls.objects.get_or_create(date=datetime.date.today(), defaults={
                'sum':v,
                'count':1,
            })
            if not created:
                obj.sum += v
                obj.count += 1
                obj.save()

class TemporaryUser(User):
    COOKIE_NAME = '_tmp_user'
    COOKIE_MAX_AGE = 5 * 365 * 24 * 3600 # 5 years
    ID_LEN = 26

    class Meta:
        proxy = True

    dirty = False

    @classmethod
    def _get_data(cls, request):
        # TODO - verify signature
        data = request.COOKIES.get(cls.COOKIE_NAME)
        try:
            data = data and json.loads(data) or {}
        except ValueError:
            data = {}
        return data
    
    @classmethod
    def _set_data(cls, response, data):
        # TODO - sign data
        domain = getattr(settings, "SESSION_COOKIE_DOMAIN", None)
        response.set_cookie(cls.COOKIE_NAME, data, max_age=cls.COOKIE_MAX_AGE, domain=domain)

    @classmethod
    def create_from_request(cls, request):
        data = cls._get_data(request)
        has_rated = data.get('has_rated')
        username = data.get('username')
        if username:
            if has_rated:
                try:
                    return cls.objects.get(
                            username=username,
                            is_active=False,
                    )
                except cls.DoesNotExist:
                    # generate new temporary user
                    pass
            else:
                return cls(username=username)

        obj = cls(username='tmp-anonymous')
        return obj

    def has_rated(self):
        return bool(self.id)

    def make_unique(self, prefix='tmp'):
        if self.username == 'tmp-anonymous':
            self.username = "%s-%s" % (prefix, hashlib.md5("%s%s%s%s" % (random.randrange(0, 2**63), os.getpid(), 
                time.time(), settings.SECRET_KEY)).hexdigest()[:self.ID_LEN])
            
        self.dirty = True

    def store_to_db(self):
        from film20.core import rating_helper
        assert not self.id
        self.make_unique()

        # for anonymouse users without id seen films are stored under key based on username
        seen_ids = rating_helper.get_seen_films(self)

        obj, created = TemporaryUser.objects.get_or_create(
                username=self.username,
                defaults={'is_active':False},
        )
        if not created:
            logger.warning("temporary user %s stored already", self.username, extra={'bg':'yellow'})
        else:
            logger.info("temporary user %s stored to db", self.username, extra={'bg':'yellow'})
        assert not obj.is_active
        self.id = obj.id
        self.dirty = True
        self.is_active = False

        if seen_ids:
            # store seen films under new key (based on user.id)
            rating_helper.mark_films_as_seen(self, seen_ids)

    def store(self, response):
        if self.dirty:
            data = json.dumps({'username':self.username, 'has_rated':bool(self.id)})
            self._set_data(response, data)

    def is_authenticated(self):
        return False

from film20.core.deferred import defer

def rating_post_save(sender, instance, created, *args, **kw):
    if instance.type == instance.TYPE_FILM and (created or
            instance.is_field_changed('rating')):
        if not settings.USE_REDIS:
            # update user ratings cache
            ratings = Rating.get_user_ratings(instance.user)
            if instance.rating:
                ratings[instance.film_id] = instance.rating
            else:
                ratings.pop(instance.film_id, None)
            cache.set(cache.Key("user_ratings", instance.user_id), ratings)

        if instance.rating:
            defer(RecomError.update, instance.user, instance.parent_id, instance.rating)

post_save.connect(rating_post_save, sender=Rating)

class UserQuerySet(QuerySet):
    def similar(self, user):
        return self.filter(compared_users__main_user=user).order_by('compared_users__score').annotate(score=models.Max('compared_users__score'))
    def active(self):
        return self.filter(is_active=True)

    def facebook_friends(self, id):
        return self.filter(fbassociation__fb_user__friends=id)

UserQuerySet.as_manager().contribute_to_class(User, 'objs')

def wrap_user_init(orig_init):
    """
    monkey patch of User constructor, to detect is_active field change
    http://jira.filmaster.org/browse/API-65
    """

    def __init__(self, *args, **kw):
        orig_init(self, *args, **kw)
        self.prev_is_active = self.is_active
    return __init__
User.__init__ = wrap_user_init(User.__init__)

def user_is_active_change(sender, instance, created, *args, **kw):
    if not created and instance.prev_is_active != instance.is_active:
        logger.info('is active changed: %s', instance.is_active)
        from film20.useractivity.models import UserActivity
        UserActivity.user_is_active_changed(instance)

post_save.connect(user_is_active_change, sender=User)

def cache_instance(sender, instance, created, *args, **kw):
    pass

post_save.connect(cache_instance)


# when someone's nick is mentioned 
#   in wall_post or comment generate notification

from film20.utils.nicknames_parser import NicknamesParser
from film20.threadedcomments.models import ThreadedComment

def parse_for_nicknames( sender, instance, created, *args, **kw ):
    if created:
        from film20.blog.models import Post
        try:
            from film20.notification import models as notification

            if isinstance( instance, ThreadedComment ):
     
                user = instance.user
                text = instance.comment
                url  = instance.content_object.get_absolute_url() + "#" + str( instance.id )
           
            elif isinstance( instance, ShortReview ):
            
                user = instance.user
                text = instance.review_text
                url  = instance.get_absolute_url()

            elif isinstance( instance, Post ):
            
                user = instance.user
                text = "%s %s" % ( instance.lead if instance.lead else '', instance.body )
                url  = instance.get_absolute_url()

                if instance.status != Object.PUBLIC_STATUS:
                    return

            else:
                return

            parser = NicknamesParser()
            parser.parse( text )

            for username in parser.usernames:
                try:
                    to_user = User.objects.get( username__iexact=username, is_active=True )
                    notification.send( [ to_user ], 
                        "username_mentioned", { "user": user, "full_url": url, "text": text } )

                except User.DoesNotExist:
                    logger.warning( "user '%s' does not exist [IGNORING]" % username )

        except ImportError, e:
            logger.error( 'Ooops, cannot import notification', e )

post_save.connect( parse_for_nicknames, sender=ShortReview, dispatch_uid="wallpost__post_save__parse_for_nicknames" )
post_save.connect( parse_for_nicknames, sender=ThreadedComment, dispatch_uid="comment__post_save___parse_for_nicknames" )
if 'film20.core.middleware.PostCommitMiddleware' in settings.MIDDLEWARE_CLASSES:
    from film20.core.middleware import PostCommitMiddleware
    post_save.connect(PostCommitMiddleware.post_save, dispatch_uid='post_commit_middleware_postsave')

