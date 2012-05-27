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
import datetime
import re

try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import render_to_string

from django.core.exceptions import ImproperlyConfigured

from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext, get_language, activate

import logging
logger = logging.getLogger(__name__)

# favour django-mailer but fall back to django.core.mail
try:
    from mailer import send_mail
except ImportError:
    from django.core.mail import send_mail

QUEUE_ALL = getattr(settings, "NOTIFICATION_QUEUE_ALL", False)

class LanguageStoreNotAvailable(Exception):
    pass

class NoticeType(models.Model):
    TYPE_NOTICE = 0
    TYPE_USER_ACTIVITY = 1
    TYPE_CHOICES = (
        (TYPE_NOTICE, _("notice")),
        (TYPE_USER_ACTIVITY, _("user activity")),
    )

    ALL_USERS = 0
    MODERATORS = 1
    USER_GROUPS = (
        (ALL_USERS, _( "all users")),
        (MODERATORS, _( "moderators")),
    )

    label = models.CharField(_('label'), max_length=64)
    display = models.CharField(_('display'), max_length=100)
    description = models.CharField(_('description'), max_length=100)

    # by default only on for media with sensitivity less than or equal to this number
    default = models.IntegerField(_('default'))
    type = models.IntegerField(_('notice_type'), choices=TYPE_CHOICES, default=TYPE_NOTICE)
    user_group = models.IntegerField(_('user group'), choices=USER_GROUPS, default=ALL_USERS)
    hidden = models.BooleanField(default=False)

    def __unicode__(self):
        return self.label

    class Meta:
        verbose_name = _("notice type")
        verbose_name_plural = _("notice types")

    @classmethod
    def is_moderator( cls, user ):
        return user.is_authenticated() and user.has_perm( 'tagging.can_edit_tags' )

from django.utils.importlib import import_module

def load_obj(path):
    module, name = path.rsplit('.', 1)
    try:
        return getattr(import_module(module), name)
    except (ImportError, AttributeError), e:
        logger.warning(e)

NOTICE_MEDIA = ()
for path in settings.NOTICE_MEDIA:
    cls = load_obj(path)
    NOTICE_MEDIA += cls and (cls(),) or ()

from media import BaseMedium

class NoticeSetting(models.Model):
    """
    Indicates, for a given user, whether to send notifications
    of a given type to a given medium.
    """

    user = models.ForeignKey(User, verbose_name=_('user'))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_('notice type'))
    medium = models.CharField(_('medium'), max_length=16, choices=((t.id, t.display) for t in NOTICE_MEDIA))
    send = models.BooleanField(_('send'))

    class Meta:
        verbose_name = _("notice setting")
        verbose_name_plural = _("notice settings")
        unique_together = ("user", "notice_type", "medium")
    
    def __unicode__(self):
        return u"%s/%s: %s" % (self.medium, self.notice_type, self.send)

class NoticeManager(models.Manager):

    def notices_for(self, user, archived=False, unseen=None, on_site=None):
        """
        returns Notice objects for the given user.

        If archived=False, it only include notices not archived.
        If archived=True, it returns all notices for that user.

        If unseen=None, it includes all notices.
        If unseen=True, return only unseen notices.
        If unseen=False, return only seen notices.
        """
        if archived:
            qs = self.filter(user=user)
        else:
            qs = self.filter(user=user, archived=archived)
        if unseen is not None:
            qs = qs.filter(unseen=unseen)
        if on_site is not None:
            qs = qs.filter(on_site=on_site)
        return qs

    def unseen_count_for(self, user):
        """
        returns the number of unseen notices for the given user but does not
        mark them seen
        """
        return self.filter(user=user, unseen=True).count()

class Notice(models.Model):
    user = models.ForeignKey(User, verbose_name=_('user'))
    message = models.TextField(_('message'))
    notice_type = models.ForeignKey(NoticeType, verbose_name=_('notice type'))
    added = models.DateTimeField(_('added'), default=datetime.datetime.now)
    unseen = models.BooleanField(_('unseen'), default=True)
    archived = models.BooleanField(_('archived'), default=False)
    on_site = models.BooleanField(_('on site'))

    objects = NoticeManager()

    def __unicode__(self):
        return self.message

    def archive(self):
        self.archived = True
        self.save()

    def is_unseen(self):
        """
        returns value of self.unseen but also changes it to false.

        Use this in a template to mark an unseen notice differently the first
        time it is shown.
        """
        unseen = self.unseen
        if unseen:
            self.unseen = False
            self.save()
        return unseen

    class Meta:
        ordering = ["-added"]
        verbose_name = _("notice")
        verbose_name_plural = _("notices")

    @models.permalink
    def get_absolute_url(self):
        return ("notification_notice", [str(self.pk)])

LANGUAGE_CODE = settings.LANGUAGE_CODE

PRIORITY_DEFAULT = 0
PRIORITY_REALTIME = 9

class NoticeQueueManager(models.Manager):
    # overridden method for FLM-306
    def get_query_set(self):
        return super(NoticeQueueManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE, priority=PRIORITY_DEFAULT).order_by('id')

class HighPriorityNoticeQueueManager(models.Manager):
    def get_query_set(self):
        return super(HighPriorityNoticeQueueManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE).exclude(priority=PRIORITY_DEFAULT).order_by('id')

class NoticeQueueBatch(models.Model):
    """
    A queued notice.
    Denormalized data for a notice.
    """
    pickled_data = models.TextField()
    priority = models.IntegerField(default=PRIORITY_DEFAULT)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#    try_cnt = models.IntegerField(default=0)
#    try_at = models.DateTimeField(blank=True, null=True)

    # language, added for FLM-306
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    objects = NoticeQueueManager()
    prio_objects = HighPriorityNoticeQueueManager()

def create_notice_type(label, display, description, default=2, type=0, user_group=0, hidden=False):
    """
    Creates a new NoticeType.

    This is intended to be used by other apps as a post_syncdb manangement step.
    """
    try:
        notice_type = NoticeType.objects.get(label=label)
        updated = False
        if display != notice_type.display:
            notice_type.display = display
            updated = True
        if description != notice_type.description:
            notice_type.description = description
            updated = True
        if default != notice_type.default:
            notice_type.default = default
            updated = True
        if type != notice_type.type:
            notice_type.type = type
            updated = True
        if user_group != notice_type.user_group:
            notice_type.user_group = user_group
            updated = True
        if hidden != notice_type.hidden:
            notice_type.hidden = hidden
            updated = True
        if updated:
            notice_type.save()
            print "Updated %s NoticeType" % label
    except NoticeType.DoesNotExist:
        NoticeType(label=label, display=display, description=description, default=default, type=type, user_group=user_group, hidden=hidden).save()
        print "Created %s NoticeType" % label

def get_notification_language(user, label=None):
    """
    Returns site-specific notification language for this user. Raises
    LanguageStoreNotAvailable if this site does not use translated
    notifications.
    """
    
    if label and label.startswith('useractivity_') or settings.NOTIFICATION_FORCE_SITE_LANG:
        # useractivities (posts on twitter/facebook/etc)
        # should be sent in site language
        # http://jira.filmaster.org/browse/FLM-759
        return settings.LANGUAGE_CODE
    
    try:
        return user.get_profile().LANG
    except Exception, e:
        lang = settings.LANGUAGE_CODE
        logger.warning('%s has no profile yet (?!), %r language will be used', user, lang)
        return lang

# TODO - add cache (invalidated if user changes notice settings)
def get_user_media(notice_type, user):
    return [m for m in NOTICE_MEDIA if m.should_send(user, notice_type)]

# queue for tests
test_queue = None

def send_now(users, label, extra_context=None, on_site=True, priority=PRIORITY_DEFAULT, now=True, **kw):
    """
    Creates a new notice.

    This is intended to be how other apps create new notices.

    notification.send(user, 'friends_invite_sent', {
        'spam': 'eggs',
        'foo': 'bar',
    )
    
    You can pass in on_site=False to prevent the notice emitted from being
    displayed on the site.
    """
    logger.debug('sending notice %r to %r, ctx:%r', label, users, extra_context)
    if extra_context is None:
        extra_context = {}
   
    notice_type = NoticeType.objects.get(label=label)
    current_language = get_language()

    for user in users:
        recipients = []
        # get user language for user from language store defined in
        # NOTIFICATION_LANGUAGE_MODULE setting

        if not QUEUE_ALL:
            try:
                user_language = get_notification_language(user)
            except LanguageStoreNotAvailable:
                user_language = settings.LANGUAGE_CODE

            activate(user_language)
        
        # reverted to original code from http://bitbucket.org/filmaster/filmaster-test/changeset/4e031d60b547/
        # as we'll be sending only current site notifications from now on, 
        # as defined in http://jira.filmaster.org/browse/FLM-306
        notices_url = settings.FULL_DOMAIN + reverse("edit_notification_settings")

        # update context with user specific translations
        context = Context({
            "user": user,
            "notice": ugettext(notice_type.display),
            "notices_url": notices_url,
            "current_site": settings.FULL_DOMAIN[7:],
            "FULL_DOMAIN": settings.FULL_DOMAIN,
            "TIME_FORMAT": settings.SCREENING_TIME_FORMAT,
        })
        context.update(extra_context)
        notice_msg = BaseMedium.render_template(notice_type, 'notice.html', context)
        notice = Notice.objects.create(user=user, message=notice_msg,
            notice_type=notice_type, on_site=on_site)

        for medium in get_user_media(notice_type, user):
            medium.send_notice(user, notice_type, context, now=now)
        
        if test_queue is not None:
            test_queue.append({
                'user': user,
                'notice_type': notice_type,
                'context': context
            })

    # reset environment to original language
    if not QUEUE_ALL:
        activate(current_language)

def send(*args, **kwargs):
    """
    A basic interface around both queue and send_now. This honors a global
    flag NOTIFICATION_QUEUE_ALL that helps determine whether all calls should
    be queued or not. A per call ``queue`` or ``now`` keyword argument can be
    used to always override the default global behavior.
    """
    queue_flag = kwargs.pop("queue", False)
    now_flag = kwargs.pop("now", False)
    assert not (queue_flag and now_flag), "'queue' and 'now' cannot both be True."
    if queue_flag:
        queue(*args, **kwargs)
        return
    elif now_flag:
        return send_now(*args, **kwargs)
    else:
        if QUEUE_ALL:
            queue(*args, **kwargs)
            return
        else:
            return send_now(*args, **kwargs)

def _send_now(users, *args, **kw):
    users = list(User.objects.filter(id__in=users))
    send_now(users, *args, **kw)
        
from film20.core.deferred import defer
def queue(users, label, extra_context=None, on_site=True, priority = PRIORITY_DEFAULT, **kw):
    """
    Queue the notification in NoticeQueueBatch. This allows for large amounts
    of user notifications to be deferred to a seperate process running outside
    the webserver.
    """
    if extra_context is None:
        extra_context = {}

    user_ids = [user.pk for user in users]

    key = lambda u:u[1]    

    userids_w_lang = [(u.pk, get_notification_language(u, label)) for u in users]
    userids_w_lang = sorted(userids_w_lang, key=key)

    delay = kw.get('delay')

    from itertools import groupby
    for lang, userids in groupby(userids_w_lang, key=key):
        ids = list(u[0] for u in userids)
        defer(_send_now, ids, label, extra_context, on_site, now=False,
              _routing_key = '%s%s.notice' % (settings.CELERY_QUEUE_PREFIX, lang),
              _delay=delay)
    
class ObservedItemManager(models.Manager):

    def all_for(self, observed, signal):
        """
        Returns all ObservedItems for an observed object,
        to be sent when a signal is emited.
        """
        content_type = ContentType.objects.get_for_model(observed)
        observed_items = self.filter(content_type=content_type, object_id=observed.id, signal=signal)
        return observed_items

    def get_for(self, observed, observer, signal):
        content_type = ContentType.objects.get_for_model(observed)
        observed_item = self.get(content_type=content_type, object_id=observed.id, user=observer, signal=signal)
        return observed_item


class ObservedItem(models.Model):

    user = models.ForeignKey(User, verbose_name=_('user'))

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    observed_object = generic.GenericForeignKey('content_type', 'object_id')

    notice_type = models.ForeignKey(NoticeType, verbose_name=_('notice type'))

    added = models.DateTimeField(_('added'), default=datetime.datetime.now)

    # the signal that will be listened to send the notice
    signal = models.TextField(verbose_name=_('signal'))

    objects = ObservedItemManager()

    class Meta:
        ordering = ['-added']
        verbose_name = _('observed item')
        verbose_name_plural = _('observed items')

    def send_notice(self):
        send([self.user], self.notice_type.label,
             {'observed': self.observed_object})


def observe(observed, observer, notice_type_label, signal='post_save'):
    """
    Create a new ObservedItem.

    To be used by applications to register a user as an observer for some object.
    """
    notice_type = NoticeType.objects.get(label=notice_type_label)
    observed_item = ObservedItem(user=observer, observed_object=observed,
                                 notice_type=notice_type, signal=signal)
    observed_item.save()
    return observed_item

def stop_observing(observed, observer, signal='post_save'):
    """
    Remove an observed item.
    """
    observed_item = ObservedItem.objects.get_for(observed, observer, signal)
    observed_item.delete()

def send_observation_notices_for(observed, signal='post_save'):
    """
    Send a notice for each registered user about an observed object.
    """
    observed_items = ObservedItem.objects.all_for(observed, signal)
    for observed_item in observed_items:
        observed_item.send_notice()
    return observed_items

def is_observing(observed, observer, signal='post_save'):
    if isinstance(observer, AnonymousUser):
        return False
    try:
        observed_items = ObservedItem.objects.get_for(observed, observer, signal)
        return True
    except ObservedItem.DoesNotExist:
        return False
    except ObservedItem.MultipleObjectsReturned:
        return True

def handle_observations(sender, instance, *args, **kw):
    send_observation_notices_for(instance)

def terminate():
    for medium in NOTICE_MEDIA:
        medium.terminate()
