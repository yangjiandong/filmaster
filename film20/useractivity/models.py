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
#-*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _, gettext
from django.db import models
from datetime import datetime, timedelta

from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.shortcuts import get_object_or_404

from film20.config import urls
from film20.core.models import Object, RatingComparator, ShortReview, Film, Person, Rating, Trailer
from film20.blog.models import Post
from film20.settings import DOMAIN
from film20.settings_defaults import SUBDOMAIN_AUTHORS
from film20.threadedcomments.models import ThreadedComment
from film20.externallink.models import ExternalLink
from film20.showtimes.models import ScreeningCheckIn, Channel, Screening
from film20.tagging.models import Tag, TaggedItem
from film20.demots.models import Demot
from film20.notification.models import send
from film20.core.urlresolvers import make_absolute_url, get_url_path, reverse as abs_reverse
from film20.utils.functional import memoize_method
from film20.utils import cache
from film20.utils.db import Model
from film20.facebook_connect.models import LikeCounter

from django.core.urlresolvers import reverse

from django.conf import settings

LANGUAGE_CODE = settings.LANGUAGE_CODE

import logging
logger = logging.getLogger(__name__)

# Create your models here.
#from film20.followers.models import Followers
from django.db.models.query_utils import Q
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from film20.utils.db import LangQuerySet
from film20.tagging.utils import parse_tag_input

class UserActivityQuerySet(LangQuerySet):
    def default_filter(self):
        return super(UserActivityQuerySet, self).default_filter()\
               .exclude(status=UserActivity.INACTIVE_STATUS).order_by('-created_at')
        
    def all_public(self):
        all = self.filter(status=UserActivity.PUBLIC_STATUS)
        all = all.exclude(activity_type=UserActivity.TYPE_FOLLOW)
#        all = all.exclude(activity_type=UserActivity.TYPE_RATING)
        return all.order_by('-created_at')

    def wall_filter(self, request):
        u = request.GET.get('u', 'all')
        f = request.GET.get('f', 'all')

        activities = self.public()

        custom_filter = None 
        if request.user.is_authenticated():
            if u == 'followed':
                activities = activities.following(request.user)
            if u == 'friends':
                activities = activities.friends(request.user)                
            if u == 'similar':
                activities = activities.similar_users(request.user)

            profile = request.user.get_profile()
            if profile and profile.custom_dashboard_filter:
                f = request.GET.get( 'f', 'custom' )
                custom_filter = { 'activity_type__in': profile.activities_on_dashboard.split( ',' ) }
                        
        filters = {
            'articles': {
                'activity_type':UserActivity.TYPE_POST,
            },
            # TODO: strange redundancy
            'reviews': {
                'activity_type':UserActivity.TYPE_POST,
            },
            'posts': {
                'activity_type':UserActivity.TYPE_SHORT_REVIEW,
            },
            'ratings': {
                'activity_type':UserActivity.TYPE_RATING,
            },
            'video': {
                'activity_type__in': (UserActivity.TYPE_LINK, 
                                      UserActivity.TYPE_TRAILER ),
                'url_kind__in':(UserActivity.VIDEO, 
                                UserActivity.TRAILER,
                                UserActivity.FULL_FEATURE,
                                UserActivity.OTHER_VIDEO ),
            },
            'images': {
                'activity_type__in':(UserActivity.TYPE_POSTER,
                                     UserActivity.TYPE_DEMOT)
            },
        }
        if custom_filter:
            filters['custom'] = custom_filter

        filter = filters.get(f)
        if filter:
            activities = activities.filter(**filter)

        activities = activities.order_by('-created_at')

        if not request.user.is_authenticated():
            activities = activities.cache("anonymouse_wall")
        
        return activities

    def film_tagged(self, tags):
        tags = parse_tag_input(tags.lower())
        out = self.filter(film__objectlocalized__LANG=settings.LANGUAGE_CODE, 
                           film__objectlocalized__tagged_items__tag__name__in=tags)
        return out
   
    def tagged(self, tags):
        tags = parse_tag_input(tags.lower())
        return self.filter(tagged_items__tag__name__in=tags)

    def public(self):
        return self.filter(status=UserActivity.PUBLIC_STATUS)
        
    def following(self, user):
        return self.users(user, following=True)
    
    def users(self, user, following=False, similar=False):
        user_list = [user]
        if following:
            user_list.extend(user.followers.following())
        if similar:
            # TODO - use score__lte=SIMILAR_USER_LEVEL
            user_list.extend(User.objs.cache().similar(user)[:50])
        return self.filter(user__in=user_list)
        
    def interesting(self):
        return self.filter(post__featured_note=True, post__is_published=True)
    
    # old methods, for compatibility with old filmaster

    def friends(self, user):
        friends_list = user.followers.friends()
        friends_list = list(friends_list)
        friends_list.append(user)
        friends = self.filter(Q(status=UserActivity.PUBLIC_STATUS),
                              Q(user__in=friends_list)).order_by("-created_at")
        return friends

    def followers(self, user):
        followers_list = user.followers.following()
        followers_list = list(followers_list)
        followers_list.append(user)
        followers = self\
                                        .filter(Q(status=UserActivity.PUBLIC_STATUS),
                                                Q(user__in=followers_list))\
                                        .order_by("-created_at")

        return followers

    def followers_notes(self, user):
        followers_list = user.followers.following()
        followers_list = list(followers_list)
        followers_list.append(user)
        followers = self\
                                        .filter(Q(status = UserActivity.PUBLIC_STATUS),
                                                Q(user__in = followers_list),
                                                Q(activity_type=UserActivity.TYPE_POST))\
                                        .order_by("-created_at")
        return followers

    def similar_users(self, user):
        similar_users_list = RatingComparator.objects.filter(main_user=user, score__lte=settings.SIMILAR_USER_LEVEL).select_related('compared_user')
        users = []
        if similar_users_list:
            for similar_user in similar_users_list:
                users.append(similar_user.compared_user)
 
        activities = self\
                                        .filter(Q(status = UserActivity.PUBLIC_STATUS),
                                                Q(user__in = users)).order_by('-created_at')
        return activities
    
    def similar_users_notes(self, user):
        activities = self.similar_users(user)
        notes = activities.filter(Q(activity_type = UserActivity.TYPE_POST))
        return notes
     
    def all_notes(self):
        notes = self\
                                    .filter(status=UserActivity.PUBLIC_STATUS)\
                                    .filter(activity_type=UserActivity.TYPE_POST)\
                                    .order_by("-created_at")
        return notes

    def draft_notes(self):
        notes = self\
                                    .filter(status=UserActivity.DRAFT_STATUS)\
                                    .filter(activity_type=UserActivity.TYPE_POST)\
                                    .order_by("-created_at")
        return notes


    def all_reviews(self):
        reviews= self\
                                    .filter(status=UserActivity.PUBLIC_STATUS)\
                                    .filter(activity_type=UserActivity.TYPE_SHORT_REVIEW)\
                                    .order_by("-created_at")
        return reviews

    def all_comments(self):
        comments= self\
                                    .filter(status=UserActivity.PUBLIC_STATUS)\
                                    .filter(activity_type=UserActivity.TYPE_COMMENT)\
                                    .order_by("-created_at")
        return comments

    def all_links(self):
        links= self\
                                    .filter(status=UserActivity.PUBLIC_STATUS)\
                                    .filter(activity_type=UserActivity.TYPE_LINK)\
                                    .order_by("-created_at")
        return links

    def all_ratings(self):
        ratings = self.filter(status=UserActivity.PUBLIC_STATUS)\
                                      .filter(activity_type=UserActivity.TYPE_RATING)\
                                      .order_by("-created_at")
        return ratings

    def all_for_user(self, user):
        """
            Returns all activites for given user
        """
        user_all = self.filter(user=user,
                status=UserActivity.PUBLIC_STATUS).order_by("-created_at")
        return user_all

    def notes_for_user(self, user):
        """
            Returns all note activites for given user
        """
        notes = self.all_notes().filter(user=user)
        return notes

    def reviews_for_user(self, user):
        """
            Returns all review activites for given user
        """
        reviews = self.all_reviews().filter(user=user)
        return reviews

    def comments_for_user(self, user):
        """
            Returns all comment activites for given user
        """
        comments = self.all_comments().filter(user=user)
        return comments

    def links_for_user(self, user):
        """
            Returns all link activites for given user
        """
        links = self.all_links().filter(user=user)
        return links

    def articles_for_user(self, user):
        """
            Returns all articles for given user
        """
        articles = self.all_notes().filter(user=user)
        return articles

    def draft_articles_for_user(self, user):
        """
            Returns all articles for given user
        """
        articles = self.draft_notes().filter(user=user)
        return articles

    def all_featured(self):
        """
            Returns all featured activites
        """
        all = self.filter(status=UserActivity.PUBLIC_STATUS, featured=True)\
                                  .order_by("-created_at")
        return all


    def all_checkins(self):
        """
            Returns all checkins activities
        """
        all = self.filter(activity_type=UserActivity.TYPE_CHECKIN)\
                                  .order_by("-created_at")
        
        return all
    
    def ratings_for_user(self, user):
        """
            Returns all rating activity for user
        """
        ratings = self.all_ratings().filter(user=user)
        return ratings

    _TYPE_MAP = {
        Post: 'post',
        ShortReview: 'short_review',
        ExternalLink: 'link',
        ScreeningCheckIn: 'checkin',
    }

    def get_for_object(self, object):
        field = self._TYPE_MAP.get(type(object))
        if field:
            return self.get(**{field:object.id})
        raise self.model.DoesNotExist("%r for %r does not exist", self.model, object)

class UserActivity(Model):

    PUBLIC_STATUS = 1
    DRAFT_STATUS = 2
    DELETED_STATUS = 3
    INACTIVE_STATUS = 4

    USERACTIVITY_STATUS_CHOICES = (
        (DRAFT_STATUS, _('Draft')),
        (PUBLIC_STATUS, _('Public')),
        (DELETED_STATUS, _('Deleted')),
        (INACTIVE_STATUS, _('Inactive')),
    )

    # externallinks kinds
    REVIEW = 1
    NEWS = 2
    BOOK = 9

    VIDEO = 3
    TRAILER = 4
    FULL_FEATURE = 5
    OTHER_VIDEO = 6

    LINK_CHOICES = (
        (REVIEW, _('Review')),
        (NEWS, _('News')),
        (BOOK, _('Book')),
        (VIDEO, _('Video')),
        (TRAILER, _('Trailer')),
        (FULL_FEATURE, _('Full feature')),
        (OTHER_VIDEO, _('Other video')),
    )

    # activity kinds
    TYPE_POST = 1
    TYPE_SHORT_REVIEW = 2
    TYPE_COMMENT = 3
    TYPE_RATING = 4
    TYPE_LINK = 5
    TYPE_FOLLOW = 6
    TYPE_CHECKIN = 7
    TYPE_POSTER = 8
    TYPE_DEMOT = 9
    TYPE_TRAILER = 10

    ACTIVITY_TYPE_CHOICES = (
        (TYPE_POST, _('post')),
        (TYPE_SHORT_REVIEW, _('Short review')),
        (TYPE_COMMENT, _('Comment')),
        (TYPE_RATING, _('Rating')),
        (TYPE_LINK, _('Link')),
        (TYPE_FOLLOW, _('Follow')),
        (TYPE_CHECKIN, _('Check in')),
        (TYPE_POSTER, _('Poster')),
        (TYPE_DEMOT, _('Demot')),
        (TYPE_TRAILER, _('Trailer')),
    )

    OBJECT_FIELD_MAP = {
            TYPE_POST: 'post',
            TYPE_SHORT_REVIEW: 'short_review',
            TYPE_COMMENT: 'comment',
            TYPE_LINK: 'link',
            TYPE_CHECKIN: 'checkin',
    }
    
    TYPE_NAME = {
            TYPE_POST: 'article',
            TYPE_SHORT_REVIEW: 'wall-post',
            TYPE_COMMENT: 'comment',
            TYPE_LINK: 'link',
            TYPE_CHECKIN: 'checkin',
            TYPE_DEMOT: 'demot',
            TYPE_TRAILER: 'trailer',
    }

    GROUPED_ACTIVITIES = (
        TYPE_LINK,
        TYPE_POSTER,
        TYPE_RATING,
        TYPE_TRAILER,
    )

    objects = UserActivityQuerySet.as_manager()

    all_objects = models.Manager()

    activity_type = models.IntegerField(_('Activity type'), choices=ACTIVITY_TYPE_CHOICES)
    # activity status
    # uses the same value as object status in core_object
    status = models.IntegerField(choices=USERACTIVITY_STATUS_CHOICES, default=PUBLIC_STATUS)
    # full link to object related to activity
    permalink = models.CharField(max_length=512, blank=True, null=True)
    user = models.ForeignKey(User, related_name="user_activity")
    username = models.CharField(_('Username'), max_length=30, null=True, blank=True)
    # object added for http://jira.jakilinux.org:8080/browse/FLM-615
    object = models.ForeignKey(Object, blank=True, null=True)

    watching_object = models.ForeignKey(Object, related_name="watching_activity", blank=True, null=True)

    post = models.ForeignKey(Post, related_name="blog_activity", null=True, blank=True)
    short_review = models.ForeignKey(ShortReview, related_name="short_review_activity", null=True, blank=True)
    comment = models.ForeignKey(ThreadedComment, related_name="comment_activity", null=True, blank=True)
    link = models.ForeignKey(ExternalLink, related_name="link_activity", null=True, blank=True)
    film = models.ForeignKey(Film, related_name="activity_film", null=True, blank=True)
    person = models.ForeignKey(Person, related_name="activity_person", null=True, blank=True)
    checkin = models.ForeignKey(ScreeningCheckIn, related_name="activity_checkin", null=True, blank=True)
    screening = models.ForeignKey(Screening, related_name="activity_screening", null=True, blank=True)
    related_rating = models.ForeignKey(Rating, related_name="activity_rating", null=True, blank=True)
    demot = models.ForeignKey(Demot, related_name="activity_demot", null=True, blank=True)
    trailer = models.ForeignKey(Trailer, related_name="activity_trailer", null=True, blank=True)
    
    title = models.CharField(_('Activity title'), max_length=200, null=True, blank=True)
    content = models.TextField(_('Activity content'), null=True, blank=True)

    # related films titles
    film_title = models.TextField(_('Related film title'), null=True, blank=True)
    # related films permalinks
    film_permalink = models.TextField(_('Related film permalink'), null=True, blank=True)
    is_tv_series = models.BooleanField(default=False)
    
    # title of wall post object (film, person or festival)
    object_title = models.TextField(_('Related object title'), null=True, blank=True)
    # url of wall post object
    object_slug = models.CharField(max_length=512, blank=True, null=True)

    # subdomain, if any
    subdomain = models.CharField(max_length=30, blank=True, null=True)
    # the end of permalink
    slug = models.CharField(max_length=512, blank=True, null=True)

    # link for externallink
    url = models.URLField(_('url'), verify_exists=False, null=True, blank=True)
    # url kind for externallink
    url_kind = models.IntegerField(_('url kind'), choices=LINK_CHOICES, default=REVIEW, null=True, blank=True)
    # video thumb for externallink
    video_thumb = models.CharField(max_length=150, blank=True, null=True)
    # whether or not it contains spoilers, used by blog post
    spoilers = models.BooleanField(_('Spoilers'), default=False)
    # mark comment as first post in forum thread
    is_first_post = models.BooleanField(_('is first post in thread'), default=False)
    # important! used to avoid count on threadedcomments table
    number_of_comments = models.IntegerField(default=0, blank=True, null=True)
    # used by checkin activity, tv station or cinema where user checkin
    channel_name = models.CharField(max_length=128, blank=True, null=True)
    channel = models.ForeignKey(Channel, blank=True, null=True)
    # checkin date
    checkin_date = models.DateTimeField(blank=True, null=True)
    
    # rating of film associated with short_review or first post's related film
    rating = models.IntegerField(blank=True, null=True)

    # is featured useractivity
    featured = models.BooleanField(_('Featured'), default=False)

    # is hidden useractivity
    hidden = models.BooleanField(_('Hidden'), default=False )
    parent = models.ForeignKey( 'self', blank=True, null=True )
    hidden_activities = models.IntegerField( default=0 )

    #timestamp
    modified_at = models.DateTimeField(_("Modified at"),default=datetime.now)
    created_at = models.DateTimeField(_("Created at"),default=datetime.now)

    #LANG
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    is_sent = models.BooleanField(default=False)
    
    tagged_items = generic.GenericRelation(TaggedItem,
                                   content_type_field='content_type',
                                   object_id_field='object_id')
    like_cnt = generic.GenericRelation(LikeCounter,
                                   content_type_field='content_type',
                                   object_id_field='object_id')

    def __unicode__(self):
        return str( self.pk )

    def __str__( self ):
        return self.__unicode__()

    def get_title(self):
        title = self.title
        if not title:
            # TODO - move this code to activity creating
            if self.activity_type == self.TYPE_RATING:
                title = "%s %s %s" % (self.user.get_profile().get_current_display_name(), _("rated"), self.film_title)
            elif self.activity_type == self.TYPE_POSTER:
                if self.film_permalink:
                    title = "%s %s %s" % (self.user.get_profile().get_current_display_name(), _("added a poster of"), self.film_title)
                else:
                    title = "%s %s %s" % (self.user.get_profile().get_current_display_name(), _("added a photo of"), self.object_title)
            elif self.activity_type == self.TYPE_SHORT_REVIEW:
                title = u"%s%s" % (_("Wall post by "), self.user.get_profile().get_current_display_name())
            elif self.activity_type == self.TYPE_TRAILER:
                title = "%s %s %s" % (self.user.get_profile().get_current_display_name(), _("added a trailer of"), self.film_title)
            elif self.activity_type == self.TYPE_FOLLOW:
                parts = self.content.split()
                title = u"%s%s%s" % (parts[0], _(" started following "), parts[2])
        return title

    def film_absolute_url(self):
        film_view = self.is_tv_series and 'show_series' or 'show_film'
        return abs_reverse(film_view, args=[self.film_permalink])

    @property
    def is_grouped( self ):
        return self.activity_type in self.GROUPED_ACTIVITIES

    def update_group( self, activity_to_add ):
        if self.activity_type == self.TYPE_POSTER:
            src = lambda o: settings.MEDIA_URL + str( o.content )
            def link(o):
                film_view = o.is_tv_series and 'show_series' or 'show_film'
                return reverse( film_view, args=[o.film_permalink] ) if o.film_permalink else reverse( 'show_person', args=[o.object_slug] )

            if self.hidden_activities == 0:
                objects = [{ 'src': src( self ), 'link': link( self ) }]
            else:
                objects = json.loads( self.content )
            objects.append({ 'src': src( activity_to_add ), 'link': link( activity_to_add )})
            self.content = json.dumps( objects )

        elif self.activity_type == self.TYPE_LINK:
            data = lambda o: { 'url': o.url, 'content': o.content, 'url_kind': o.url_kind,
                    'video_thumb': o.video_thumb,'film_title': o.film_title, 'film_permalink': o.film_permalink, 'is_tv_series': o.is_tv_series }
            if self.hidden_activities == 0:
                objects = [ data( self ) ]
            else:
                objects = json.loads( self.content )
            objects.append( data( activity_to_add ) )
            self.content = json.dumps( objects )

        elif self.activity_type == self.TYPE_TRAILER:
            data = lambda o: { 'url': o.url, 'content': o.content, 'video_thumb': o.video_thumb, 'film_title': o.film_title, 'film_permalink': o.film_permalink, 'is_tv_series': o.is_tv_series }
            if self.hidden_activities == 0:
                objects = [ data( self ) ]
            else:
                objects = json.loads( self.content )
            objects.append( data( activity_to_add ) )
            self.content = json.dumps( objects )

        elif self.activity_type == self.TYPE_RATING:
            self.content = str( self.hidden_activities + 1 )

        self.hidden_activities += 1
        self.save()

    def get_json_content( self ):
        try:
            return json.loads( self.content )
        except Exception:
            return [] 

    def get_comment_title(self):
        return self.get_title()

    def get_kind(self):
        for choice in self.ACTIVITY_TYPE_CHOICES:
            if self.activity_type == choice[0]:
               return choice[1]

    def get_url_kind(self):
        for choice in self.LINK_CHOICES:
            if self.url_kind == choice[0]:
               return choice[1]

    def get_absolute_url(self):
        slug = self.get_slug()
        if slug:
            return make_absolute_url(slug)
        return self.permalink

    def get_slug(self):
        if self.activity_type == self.TYPE_POSTER:
            return reverse('show_poster', args=[self.username, self.id])
        if self.activity_type == self.TYPE_DEMOT:
            return reverse('show_demot', args=[self.username, self.id])
        if self.activity_type == self.TYPE_RATING:
            return reverse('show_rating', args=[self.username, self.id])
        if self.activity_type == self.TYPE_TRAILER:
            return reverse('show_trailer', args=[self.username, self.id])
        if self.subdomain:
            return "/%s/%s%s" % (urls.urls['SHOW_PROFILE'], self.subdomain, self.slug)
        if self.slug == 'LEGACY_FORUM_COMMENT':
            return '#'
        return self.slug

    def get_object_url(self):
        assert self.object_slug
        return make_absolute_url(self.object_slug)

    def api_object_uri(self):
        from film20.api.api_1_1.handlers import UserActivityHandler
        uri = UserActivityHandler.object_uri(self)
        return uri
    
    def api_resource_uri(self):
        from film20.api.api_1_1.handlers import UserActivityHandler
        uri = UserActivityHandler.resource_uri(self)
        return uri
   
    def get_object(self):
        field = self.OBJECT_FIELD_MAP.get(self.activity_type)
        return field and getattr(self, field)

    def get_type_name(self):
        return self.TYPE_NAME.get(self.activity_type, '')

    @classmethod
    def user_is_active_changed(cls, user):
        objects = cls.all_objects.filter(user=user)
        if user.is_active:
            objects.filter(status=cls.INACTIVE_STATUS).update(status=cls.PUBLIC_STATUS)
        else:
            objects.filter(status=cls.PUBLIC_STATUS).update(status=cls.INACTIVE_STATUS)

    @property
    def extra_films_rated_count(self):
        try:
            if self.activity_type == self.TYPE_RATING:
                return int(self.content)
        except ValueError:
            pass
        return 0
    
    def update_tags(self):
        obj = self.get_related_object()
        films = obj and obj.get_related_films() or ()
        if not obj and self.activity_type == self.TYPE_RATING and \
                self.film:
            films = (self.film, )
        
        tags = set()

        if obj:
            tags.update(Tag.objects.get_for_object(obj))
        logger.debug("rel object tags: %r", tags)
        if films:
            film_tags = set()
            for f in films:
                localized = f.get_localized_object()
                if not localized: 
                    continue
                t = Tag.objects.get_for_object(localized)
                if film_tags:
                    film_tags.intersection_update(t)
                else:
                    film_tags.update(t)
            logger.debug("rel object film tags: %r", film_tags)
            tags.update(film_tags)

        Tag.objects.update_tags(self, ','.join(unicode(t) for t in tags))

    def get_related_object(self):
        return self.short_review or self.post or self.link or self.checkin # comment ?

    @classmethod
    def get_hashtags(self, film):
        if not film:
            return ''
        loc = film.get_localized_object()
        from film20.festivals.models import Festival
        festival_tags = dict( (f.tag.lower(), f.hashtag) for f in Festival.get_open_festivals() )
        film_tags = [t.strip() for t in (film.get_tags() or '').split(',') if t.strip()]
        hash_tags = [festival_tags.get(t.lower()) for t in film_tags]
        return ' '.join('#'+t for t in hash_tags if t)

    def send_notice(self):
        if self.post != None:
            film = list(self.post.related_film.all()[0:1])
            film = film and film[0]
            person = list(self.post.related_person.all()[0:1])
            person = person and person[0]
            object = film or person
            send([self.user], "useractivity_post", {
                'post':self.post,
                'link':self.post.get_absolute_url(),
                'picture':object and object.get_absolute_image_url() or '',
                'film':film,
                'film_kind': gettext("TV series") if film and film.is_tv_series else gettext("film"),
                'person':person,
                'object':object,
                'hashtags': self.get_hashtags(film),
            })
        elif self.short_review != None:
            # TODO write notifications for wall posts!
            if self.short_review.object is not None and \
               self.short_review.object.type == Object.TYPE_FILM:
                self.object = self.short_review.parent
                self.watching_object = self.short_review.parent
                send([self.user], "useractivity_short_review", {
                    'short_review':self.short_review,
                    'link':self.short_review.get_absolute_url(),
                    'picture':self.short_review.object.film.get_absolute_image_url(),
                    'film':self.short_review.object.film,
                    'hashtags': self.get_hashtags(self.short_review.object.film)
                })
        elif self.comment != None:
            # for comments, create notification objects!
            Watching.create_notices(self)

    @classmethod
    def pre_save(cls, sender, instance, **kw):
        logger.debug("About to save an activity")
        instance.modified_at = datetime.now()

        if instance.post != None:
            instance.object = instance.post.parent
            instance.watching_object = instance.post.parent
        elif instance.short_review != None:
            instance.object = instance.short_review.parent
            instance.watching_object = instance.short_review.parent
            if instance.short_review.object:
                instance.object_title = instance.short_review.get_title()
                instance.object_url = instance.short_review.object.get_child_absolute_url()
        elif instance.comment != None:
            # content_object should be pointing to Thread
            if isinstance(instance.comment.content_object, Object):
                instance.object = instance.comment.parent_object
                instance.watching_object = instance.comment.content_object
        elif instance.link != None:
            instance.object = instance.link.parent
            instance.watching_object = instance.link.parent
        
        logger.debug("About to add a watcher to an activity")

        if instance.short_review != None:
            if instance.short_review.object:
                instance.object_title = instance.short_review.get_title()
                instance.object_slug= get_url_path(instance.short_review.object.get_child_absolute_url())
        elif instance.film:
            instance.object_title = instance.film.get_title()
            instance.object_slug = get_url_path(instance.film.get_absolute_url())

        if instance.film:
            instance.is_tv_series = instance.film.is_tv_series
        if instance.checkin:
            instance.screening_id = instance.checkin.screening_id

        if not instance.user.is_active and instance.status == UserActivity.PUBLIC_STATUS:
            instance.status = UserActivity.INACTIVE_STATUS

        # notice is not sent and instance status is public, so send it (and mark as sent)
        instance._send_notice = not instance.is_sent and instance.status == UserActivity.PUBLIC_STATUS

        instance.is_sent = instance.is_sent or instance._send_notice
        
        obj = instance.get_object()
        if obj:
            instance.slug = obj.get_slug()
            instance.subdomain = None

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kw):
        Watching.add_watching(instance)
        
        if getattr(instance, '_update_tags', True):
            instance.update_tags()
        if getattr(instance, '_send_notice', False):
            instance.send_notice()
    
        # group activities
        if created and instance.is_grouped:
            period = settings.USERACTIVITY_GROUPING_PERIOD
            tm = datetime.now() - timedelta( seconds=period )
            objects = cls.all_objects.filter( 
                LANG=instance.LANG,
                user=instance.user, 
                activity_type=instance.activity_type, 
                created_at__gte=tm, hidden=False
            ).exclude( pk=instance.pk ).order_by( 'created_at' )

            if len( objects ):
                parent = objects[0]
                parent.update_group( instance )

                instance.parent = parent
                instance.hidden = True
                instance.save()
            
            else:
                from film20.useractivity.signals import grouping_started
                grouping_started.send( sender=instance, instance=instance )
                
                eta = datetime.now() + timedelta( seconds=period + 10 )
                notify_grouping_finished.apply_async( args=[ instance ], eta=eta )
    
    def is_commentable(self):
        return self.activity_type in (
                self.TYPE_POST,
                self.TYPE_SHORT_REVIEW,
                self.TYPE_RATING,
                self.TYPE_LINK,
                self.TYPE_CHECKIN,
                self.TYPE_POSTER,
                self.TYPE_DEMOT,
                self.TYPE_TRAILER,
                self.TYPE_FOLLOW,
        )

    @memoize_method
    def _get_festival_names(self):
        """
            return list of (short_name, name) tuples of associated festivals
        """
        from film20.festivals.models import Festival
        festivals = dict((f.tag, (f.short_name or f.name, f.name)) for f in Festival.get_open_festivals())
        tags = set(t.name for t in Tag.objects.get_for_object(self))
        tags.intersection_update(festivals.keys())
        return [ festivals[t] for t in tags ]

    def title_prefix(self):
        return ' '.join("[%s]" % t[0] for t in self._get_festival_names())

    def descr_prefix(self):
        return ' '.join("[%s]" % t[1] for t in self._get_festival_names())

    def can_remove( self, user ):
        """
            returns True if given user can remove activity
        """
        return user.is_authenticated() and not self.number_of_comments > 0 and( user.is_superuser or user.pk == self.user.pk )

    def remove( self, user ):
        if self.can_remove( user ):
            self.status = self.DELETED_STATUS
            self.save()
            return True
        return False

models.signals.pre_save.connect(UserActivity.pre_save, sender=UserActivity)
models.signals.post_save.connect(UserActivity.post_save, sender=UserActivity)

def change_user_display_name(user):
    logger.info("check display name for user %s" % user)
    from film20.core.models import Profile
    profile = Profile.objects.get(user = user)
    logger.info("get profile: %s" % profile)
    key = cache.Key("display_name_profile", user.id)
    cache.delete(key)
    logger.info("end of username changes")

class Watching(models.Model):
    """
        Users can subcribe to receive all activity (comments) for objects like blog posts,
        short reviews or forum threads. This class store tha information about those 
        subscriptions either automatic or manual
    """
    
    # object being watched
    # nullable params removed for http://jira.filmaster.org/browse/FLM-461
    object = models.ForeignKey(Object, null=True, default=None)

    activity = models.ForeignKey(UserActivity, null=True)

    # watching user
    user = models.ForeignKey(User, related_name="watching_user")
    
    # watching-related fields
    TYPE_STARTED_BY_USER = 1
    TYPE_USER_COMMENTED = 2
    TYPE_USER_SUBSCRIBED = 3
    
    WATCHING_TYPE_CHOICES = (
        (TYPE_STARTED_BY_USER, 'Started by user'),
        (TYPE_USER_COMMENTED,'User commented'),   
        (TYPE_USER_SUBSCRIBED,'User subscribed'),   
    )
    
    watching_type = models.IntegerField(_('Watching type'), choices=WATCHING_TYPE_CHOICES, null=False, blank=False)
    
    # user selected to observe/no observe this object
    is_observed = models.BooleanField()
    # if automatically subscribed (all threads, posts, short reviews are automatically subscribed)
    is_auto = models.BooleanField()
    
    # timestamp
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    @classmethod
    def subscribe(cls, activity, user, is_observed=True):
        watching, created = Watching.objects.get_or_create(
                user=user,
                activity=activity,
                defaults = {
                    'is_auto':False,
                    'is_observed': is_observed,
                    'watching_type': Watching.TYPE_USER_SUBSCRIBED,
                },
        )
        if not created:
            watching.is_observed = is_observed
            watching.save()
        
        return watching

    @classmethod
    def is_subscribed(cls, activity, user):
        try:
            watching = Watching.objects.get(activity=activity, user=user)
            is_observed = watching.is_observed
        except Watching.DoesNotExist, e:
            is_observed = False

        return is_observed

    @classmethod
    def add_watching(cls, activity):
        """
            adds or updates a Watching for an object related to the activity
        """
        if activity.activity_type == UserActivity.TYPE_COMMENT:
            watching_object = activity.comment.content_object
            if not isinstance(watching_object, UserActivity):
                logger.warning("commented object is not UserActivity - ignoring")
                return
            watching_type = Watching.TYPE_USER_COMMENTED
        elif activity.is_commentable():
            watching_object = activity
            watching_type = Watching.TYPE_STARTED_BY_USER
        else:
            logger.debug("Non-watchable activity type detected. Ignoring.")
            return
        if not watching_object:
            logger.warning("Activity without related object? Ignoring.")
            return

        watching, created = Watching.objects.get_or_create(
                user=activity.user, 
                activity=watching_object,
                defaults=dict(
                    watching_type=watching_type,
                    is_auto=True,
                    is_observed=True,
                ))
        return watching

    @classmethod
    def create_notices(cls, activity):
        from notification import models as notification

        if activity.comment == None:
            logger.warning("Comment is null - something went wrong")
            return
       
        watching_object = activity.comment.content_object
        if not isinstance(watching_object, UserActivity):
            logger.warning("commented object is not UserActivity, ignoring")
            return
        
        reply_url = activity.comment.get_absolute_url()
        title = watching_object.get_title()
        
        # get all users listening to current post/thread
        watchings = Watching.objects.filter(
                activity=watching_object,
                is_observed=True)
        
        # create notices with a new reply to all of those
        for watching in watchings:
            if watching.user != activity.user:
                # we do not save activity, because this is called from within save
                notification.send([watching.user], "reply",
                    {
                        'from_user': activity.user,
                        'reply_text': activity.comment.comment,
                        'comment':activity.comment,
                        'reply_url': reply_url,
                        'title': title
                    }
                )

    # TODO - moved from WatchingHelper, but it doesnt work
    @classmethod
    def recent_answers(cls, user):
        # all comment activities
        comments = UserActivity.objects.filter(
            activity_type = UserActivity.TYPE_COMMENT)
        # but not the ones by the user
        comments = comments.exclude(user = user)
        # and only those relating to the threads that the user is watching
        comments = comments.extra(            
            join=['LEFT JOIN "useractivity_watching" ON ("useractivity_watching"."object_id" = "useractivity_useractivity"."watching_object_id")'],
            where=['("useractivity_watching"."is_observed"=true AND "useractivity_watching"."user_id" = %i)' % user.id],
        )
        # order by / limit 
        comments = comments.order_by("-created_at")
        return comments


from celery.task import task

@task
def notify_grouping_finished( activity ):
    from film20.useractivity.signals import grouping_finished
    grouping_finished.send( sender=activity, instance=activity )
