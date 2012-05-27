#!/usr/bin/python
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

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic

import logging
logger = logging.getLogger(__name__)

class FBObject(models.Model):
    class Meta:
        abstract = True

    id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=128)
    link = models.URLField(verify_exists=False, null=True, blank=True)
    
    @classmethod
    def get_fields(cls):
        return [f.name for f in cls._meta.fields if isinstance(f, (models.CharField, models.URLField))]
    
    def __unicode__(self):
        return "%s: %s" % (self.id, self.name)

    def __eq__(self, other):
        return other and self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @classmethod
    def create_or_update(cls, data):
        fields = cls.get_fields()
        defaults = dict(i for i in data.items() if i[0] in fields)
        obj, created = cls.objects.get_or_create(id=data['id'], defaults=defaults)
        if not created and any(defaults.get(f) != getattr(obj, f) for f in defaults.keys()):
            for k, v in defaults.items():
                setattr(obj, k, v)
            obj.save()
        return obj

    @classmethod
    def update_objects(cls, api, path, relation):
        prev = set(relation.all())
        current = set()

        while True:
            objs = api.get(path, fields=','.join(cls.get_fields()))
            for f in objs.get('data', ()):
                obj = cls.create_or_update(f)
                current.add(obj)

            paging = objs.get('paging')
            path = paging and paging.get('next')
            if not path:
                break

        relation.add(*list(current - prev))
        relation.remove(*list(prev - current))

from film20.core.models import Film

class FBMovie(FBObject):
    website = models.TextField(null=True, blank=True)
    picture = models.URLField(verify_exists=False, null=True, blank=True)
    
    film = models.ForeignKey(Film, null=True, blank=True)

    def save(self, *args, **kw):
        if not self.film_id:
            # try to match
            from .url_matcher import URLMatcher
            film_data = URLMatcher.fetch(self.link)
            self.film = film_data and film_data.match_film()
            if not self.film:
                priority = -1
                if self.id:
                    cnt = self.fbuser_set.count()
                    priority = (cnt / 5) - 1
                from film20.showtimes.models import FilmOnChannel
                foc, created = FilmOnChannel.objects.get_or_create(key=self.link, source='facebook', defaults={
                    'directors': film_data and ','.join(film_data.directors),
                    'title': film_data and film_data.title or '',
                    'priority': priority,
                })
                if foc.film:
                    self.film = foc.film

        return super(FBMovie, self).save(*args, **kw)

    @classmethod
    def on_film_rematched(cls, sender, instance, *args, **kw):
        if instance.source == 'facebook' and instance.film:
            cls.objects.filter(link = instance.key).update(film=instance.film)

from film20.showtimes.signals import film_rematched
film_rematched.connect(FBMovie.on_film_rematched, dispatch_uid="on_fbmovie_remached_sig")

class FBUser(FBObject):
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    username = models.CharField(max_length=128, null=True, blank=True)

    gender = models.CharField(max_length=20, null=True, blank=True)
    locale = models.CharField(max_length=10, null=True, blank=True)

    friends = models.ManyToManyField('self', symmetrical=True, null=True, blank=True)
    movies = models.ManyToManyField(FBMovie, null=True, blank=True)

    def picture_url(self, type='square'):
        return "http://graph.facebook.com/%s/picture?type=%s" % (self.id, type)

class FBRequest(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    data = models.CharField(max_length=255)
    sender = models.ForeignKey(User)

class FBAssociation(models.Model):
    """
    Assoction of user accounts and Facebook Accounts
    """
    user = models.ForeignKey(User, verbose_name=_('User'), unique=True)
    fb_uid = models.CharField(max_length=100, verbose_name=_('Facebook ID'), unique=True)

    fb_user = models.ForeignKey(FBUser, null=True, blank=True)

    is_new = models.BooleanField(verbose_name=_('Is new user'), blank=True, default=False)
    is_from_facebook = models.BooleanField(verbose_name=_('Is from Facebook'), default=True, blank=True)
    access_token = models.CharField(max_length=128, verbose_name=_('Facebook Access Token'), null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    STATUS_INITIAL = 0
    STATUS_SYNC_OK = 1

    status = models.IntegerField(default=STATUS_INITIAL, null=True)

    def __str__(self):
        return str(self.fb_uid)
    
    def __unicode__(self):
        return str(self.fb_uid)
    
    class Meta:
        verbose_name = _('Facebook association')
        verbose_name_plural = _('Facebook associations')

    def sync_with_fb(self):
        from .graph import API
        api = API(self.access_token)
        try:
            me = api.get('/me')

            assert me['id'] == self.fb_uid

            user = FBUser.create_or_update(me)

            if not self.fb_user_id:
                self.fb_user=user

            FBUser.update_objects(api, '/me/friends', user.friends)
            FBMovie.update_objects(api, '/me/movies', user.movies)
            self.status = self.STATUS_SYNC_OK
        except urllib2.HTTPError, e:
            self.status = e.code
        self.save()

    @classmethod
    def _sync_with_fb(cls, id):
        assoc = cls.objects.select_related().get(id=id)
        assoc.sync_with_fb()

        if assoc.fb_user_id:
            from film20.notification.models import send
            from film20.core.urlresolvers import reverse as abs_reverse

            friends = User.objs.active().facebook_friends(assoc.fb_user_id)
            send(friends, "friends_joined", {
                'user': assoc.user,
                'fb_user': assoc.fb_user,
                'network': 'Facebook',
                'profile_url': abs_reverse('show_profile', args=[assoc.user.username]),
            })
            for friend in friends:
                assoc.user.followers.follow(friend)

    @classmethod
    def post_commit(cls, sender, instance, created, *args, **kw):
        if created:
            from film20.core.deferred import defer
            defer(instance._sync_with_fb, instance.id)

from film20.core.signals import post_commit
post_commit.connect(FBAssociation.post_commit, sender=FBAssociation, dispatch_uid=FBAssociation.post_commit)

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

import json
import urllib2
from urllib import urlencode

class LikeCounter(models.Model):
    likes = models.IntegerField(null=True, blank=True)
    shares = models.IntegerField(null=True, blank=True)
    
    like_count = models.IntegerField(default=0, null=True, blank=True)
    share_count = models.IntegerField(default=0, null=True, blank=True)
    comment_count = models.IntegerField(default=0, null=True, blank=True)
    total_count = models.IntegerField(default=0, null=True, blank=True)
    click_count = models.IntegerField(default=0, null=True, blank=True)

    url = models.URLField(verify_exists=False, unique=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        unique_together = ('content_type', 'object_id')

    def __repr__(self):
        return u"<LikeCounter %r: %s>" % (self.object, self.total_count)

    @classmethod
    def update(cls, url, content_type, object_id):
        app_label, model = content_type.split('.')
        ctype = ContentType.objects.get_by_natural_key(app_label, model)
        object = ctype.get_object_for_this_type(pk=object_id)
        return cls.update_for_object(object)

    @classmethod
    def update_for_object(cls, object):
        url = object.get_absolute_url()

        data = json.loads(urllib2.urlopen(
            "https://graph.facebook.com/fql?q=SELECT%%20url,%%20normalized_url,%%20share_count,%%20like_count,%%20comment_count,%%20total_count,commentsbox_count,%%20comments_fbid,%%20click_count%%20FROM%%20link_stat%%20WHERE%%20url='%s'" % urlencode({'url': url})[4:]).read()).get('data')

        stats = data and data[0]
        if not stats:
            return
        cnt, created = LikeCounter.objects.get_or_create(
                url=url,
                defaults={
                    'object': object,
                    'like_count': stats.get('like_count'),
                    'share_count': stats.get('share_count'),
                    'comment_count': stats.get('comment_count'),
                    'total_count': stats.get('total_count'),
                    'click_count': stats.get('click_count'),
                })

        if not created:
            cnt.like_count = stats.get('like_count')
            cnt.share_count = stats.get('share_count')
            cnt.comment_count = stats.get('comment_count')
            cnt.total_count = stats.get('total_count')
            cnt.click_count = stats.get('click_count')
            cnt.save()

# hack - moved here (from Film class) to avoid circular import
generic.GenericRelation(LikeCounter, content_type_field='content_type', object_id_field='object_id').contribute_to_class(Film, 'like_cnt')

