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
from django.db import models
from django.conf import settings
from django.db.models import signals, get_app
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from film20.utils import cache_helper as cache
from film20.utils.db import QuerySet

import logging
logger = logging.getLogger(__name__)

class MessageManager(models.Manager):

    def inbox_for(self, user):
        """
        Returns all messages that were received by the given user and are not
        marked as deleted.
        """
        return self.filter(
            recipient=user,
            recipient_deleted_at__isnull=True,
        )

    def outbox_for(self, user):
        """
        Returns all messages that were sent by the given user and are not
        marked as deleted.
        """
        return self.filter(
            sender=user,
            sender_deleted_at__isnull=True,
        )

    def trash_for(self, user):
        """
        Returns all messages that were either received or sent by the given
        user and are marked as deleted.
        """
        return self.filter(
            recipient=user,
            recipient_deleted_at__isnull=False,
        ) | self.filter(
            sender=user,
            sender_deleted_at__isnull=False,
        )
    
class Message(models.Model):
    """
    A private message from user to user
    """
    subject = models.CharField(_("Subject"), max_length=120)
    body = models.TextField(_("Body"))
    sender = models.ForeignKey(User, related_name='sent_messages', verbose_name=_("Sender"))
    recipient = models.ForeignKey(User, related_name='received_messages', null=True, blank=True, verbose_name=_("Recipient"))
    parent_msg = models.ForeignKey('self', related_name='next_messages', null=True, blank=True, verbose_name=_("Parent message"))
    conversation = models.ForeignKey('Conversation', related_name='messages', null=True, blank=True, verbose_name=_("Conversation"))
    sent_at = models.DateTimeField(_("sent at"), null=True, blank=True, auto_now_add=True)
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)
    replied_at = models.DateTimeField(_("replied at"), null=True, blank=True)
    sender_deleted_at = models.DateTimeField(_("Sender deleted at"), null=True, blank=True)
    recipient_deleted_at = models.DateTimeField(_("Recipient deleted at"), null=True, blank=True)
    
    objects = MessageManager()
    
    def mark_as_read(self):
        if self.read_at is None:
            self.read_at = datetime.datetime.now()
            self.save()
            if self.conversation:
                # decrement conversation unread cnt for message recipient
                if self.recipient_id == self.conversation.recipient_id:
                    self.conversation.recipient_unread_cnt = max(self.conversation.recipient_unread_cnt - 1, 0)
                if self.recipient_id == self.conversation.sender_id:
                    self.conversation.sender_unread_cnt = max(self.conversation.sender_unread_cnt - 1, 0)
                self.conversation.save()

    def new(self):
        """returns whether the recipient has read the message or not"""
        return self.read_at is None
        
    def replied(self):
        """returns whether the recipient has written a reply to this message"""
        if self.replied_at is not None:
            return True
        return False
    
    def __unicode__(self):
        return self.subject
    
    def get_subject(self):
        return (self.subject or '').strip() or _('no subject')

    def get_absolute_url(self):
        return reverse('messages_view_conversation', args=[self.conversation_id]) + '#message_%s' % self.id

    def delete_by(self, user, update_conversation=True):
        now = datetime.datetime.now()
        c1 = user == self.sender and not self.sender_deleted_at
        c2 = user == self.recipient and not self.recipient_deleted_at
        if c1 or c2:
            if c1:
                self.sender_deleted_at = now
            if c2:
                self.recipient_deleted_at = now
            self.save()
            if update_conversation and self.conversation:
                self.conversation.inc_msg_cnt(user, -1)
                if not self.read_at:
                    self.conversation.inc_unread_cnt(user, -1)
                self.conversation.save()
            return True

    def undelete_by(self, user, update_conversation=True):
        c1 = user == self.sender and self.sender_deleted_at
        c2 = user == self.recipient and self.recipient_deleted_at
        if c1 or c2:
            if c1:
                self.sender_deleted_at = None
            if c2:
                self.recipient_deleted_at = None
            self.save()
            if update_conversation and self.conversation:
                self.conversation.inc_msg_cnt(user, 1)
                if not self.read_at:
                    self.conversation.inc_unread_cnt(user, 1)
                self.conversation.save()
            return True
    
    def fix(self, level=0):
        if not self.conversation_id:
            if self.parent_msg:
                # make sure parent is fixed
                self.parent_msg.fix(level+1)
                conversation = self.parent_msg.conversation
                conversation.sender_cnt += 1
                conversation.recipient_cnt += 1
            else:
                conversation = Conversation()
                conversation.sender_cnt = 1
                conversation.recipient_cnt = 1
                conversation.sender = self.sender
                conversation.recipient = self.recipient

            if self.read_at is None and self.recipient_deleted_at is None:
                conversation.inc_unread_cnt(self.recipient, 1)
            if self.replied_at is not None:
                conversation.is_replied = True

            conversation.subject = self.subject
            conversation.body = self.body
            conversation.last_sender = self.sender
            conversation.updated_at = self.sent_at
            conversation.save()

            self.conversation=conversation
            self.save()
            
            print ' '*level, "FIXED"

    @classmethod
    def fix_all(cls):
        while True:
            q=cls.objects.filter(conversation__isnull=True).order_by('sent_at')
            item = list(q[0:1])
            item = item and item[0]
            if not item:
                break
            item.fix()

        total = Conversation.objects.count()
        cnt = 0

        for c in Conversation.objects.all():
            last_msg = c.messages.order_by('-sent_at')
            last_msg = last_msg and last_msg[0]
            if last_msg:
                c.updated_at = last_msg.sent_at
            c.is_replied = bool(c.messages.filter(replied_at__isnull=False))
            c.save()
            cnt += 1
            print cnt, '/', total

    def save(self, force_insert=False, force_update=False):
        if not self.id:
            if self.parent_msg:
                conversation = self.parent_msg.conversation
                # parent_msg.conversation is not None only for new conversations
                if conversation:
                    conversation.sender_cnt += 1
                    conversation.recipient_cnt += 1
                if self.recipient_id == self.parent_msg.sender_id:
                    self.parent_msg.replied_at = datetime.datetime.now()
                    self.parent_msg.save()
                    conversation.is_replied = True
            else:
                conversation = Conversation()
                conversation.sender_cnt = 1
                conversation.recipient_cnt = 1
                conversation.sender = self.sender
                conversation.recipient = self.recipient

            if conversation:
                conversation.inc_unread_cnt(self.recipient, 1)
                conversation.subject = self.subject
                conversation.body = self.body
                conversation.last_sender = self.sender
                conversation.updated_at = self.sent_at or datetime.datetime.now()
                conversation.save()
                self.conversation = conversation
            
        super(Message, self).save(force_insert, force_update) 
    
    @classmethod
    def send(cls, sender, recipients, subject, body, parent_msg=None):
        message_list = []
        for r in recipients:
            msg = cls(
                sender = sender,
                recipient = r,
                subject = subject,
                body = body,
                parent_msg = parent_msg,
                sent_at = datetime.datetime.now()
            )
            msg.save()
            message_list.append(msg)
            if notification:
                replied = msg.parent_msg and (msg.recipient_id == msg.parent_msg.sender_id)
                if replied:
                    notification.send([sender], "messages_replied", {'message': msg,})
                    notification.send([r], "messages_reply_received", {'message': msg,}, priority=notification.PRIORITY_REALTIME)
                else:
                    notification.send([sender], "messages_sent", {'message': msg,})
                    notification.send([r], "messages_received", {'message': msg,}, priority=notification.PRIORITY_REALTIME)
        return message_list

    class Meta:
        ordering = ['-sent_at']
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")

class ConversationQuerySet(QuerySet):
    def default_filter(self):
        return self.order_by('-updated_at')

    def user_conversations(self, user, replied=False):
        extra = replied and {'is_replied':True} or {}
        query = self.filter(models.Q(sender=user, sender_cnt__gt=0, **extra) | \
                            models.Q(recipient=user, recipient_cnt__gt=0))
        return query._clone(user=user)

    def unread_counter(self, user):
        key = cache.Key("conversation_unread_counter", user.id)
        cnt = cache.get(key)
        if cnt is None:
            query = self.filter(models.Q(sender=user, sender_cnt__gt=0, sender_unread_cnt__gt=0) | \
                                models.Q(recipient=user, recipient_cnt__gt=0, recipient_unread_cnt__gt=0))
            cnt = query.distinct().count()
            cache.set(key, cnt)
        return cnt

    def iterator(self):
        items = super(ConversationQuerySet, self).iterator()
        def _fix(self, item):
            if hasattr(self, 'user'):
                item.user = self.user
            return item
        return (_fix(self, i) for i in items)
    
    def _clone(self, *args, **kw):
        ret = super(ConversationQuerySet, self)._clone(*args, **kw)
        if not hasattr(ret, 'user') and hasattr(self, 'user'):
            ret.user = self.user
        return ret
    

class Conversation(models.Model):
    sender = models.ForeignKey(User, related_name="sent_conversations")
    recipient = models.ForeignKey(User, related_name="received_conversations")

    last_sender = models.ForeignKey(User)
    subject = models.CharField(_("Subject"), max_length=120)
    body = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("sent at"), auto_now_add=True)

    sender_cnt = models.IntegerField(default=0, null=False, blank=False)
    recipient_cnt =models.IntegerField(default=0, null=False, blank=False)

    sender_unread_cnt = models.IntegerField(default=0, null=False, blank=False)
    recipient_unread_cnt =models.IntegerField(default=0, null=False, blank=False)
    
    is_replied = models.BooleanField(default=False)
    
    objects = ConversationQuerySet.as_manager()
    
    class Meta:
        ordering = ('-updated_at',)
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")

    def user_messages(self, user):
        return self.messages.exclude(sender_deleted_at__isnull=False, sender=user)\
                            .exclude(recipient_deleted_at__isnull=False, recipient=user)\
                            .order_by('sent_at')

    def delete_by(self, user):
        for msg in self.messages.all():
            msg.delete_by(user, update_conversation=False)
        if user == self.sender:
            self.sender_cnt = 0
            self.sender_unread_cnt = 0
        if user == self.recipient:
            self.recipient_cnt = 0
            self.recipient_unread_cnt = 0
        self.save()

    def undelete_by(self, user):
        cnt = 0
        unread_cnt = 0
        for msg in self.messages.all():
            undeleted = msg.undelete_by(user, update_conversation=False)
            cnt += 1
            unread_cnt += bool(undeleted and not msg.read_at)
                
        if user == self.sender:
            self.sender_cnt = cnt
            self.sender_unread_cnt += unread_cnt
        if user == self.recipient:
            self.recipient_cnt = cnt
            self.recipient_unread_cnt += unread_cnt
        self.save()
    
    def inc_msg_cnt(self, user, delta):
        if user == self.sender:
            self.sender_cnt = max(0, self.sender_cnt + delta)
        if user == self.recipient:
            self.recipient_cnt = max(0, self.recipient_cnt + delta)
    
    def inc_unread_cnt(self, user, delta):
        if user == self.sender:
            self.sender_unread_cnt = max(0, self.sender_unread_cnt + delta)
        if user == self.recipient:
            self.recipient_unread_cnt = max(0, self.recipient_unread_cnt + delta)

    def threaded_messages(self, user):
        cache_key = "conversation_thread_%s" % self.pk
        thread = cache.get(cache_key)
        if thread is not None:
            return thread
        query = self.messages.order_by('id')
        messages = {}
        root = None
        for msg in query:
            msg.children = []
            messages[msg.id] = msg    
            if msg.parent_msg_id:
                parent = messages.get(msg.parent_msg_id)
                if parent:
                     msg.level = parent.level + 1
                     parent.children.append(msg)
            else:
                msg.level = 0
                root = msg

	def traverse(root):
	    yield root
	    for c in root.children:
	        for i in traverse(c):
	            yield i

        def not_deleted(msg):
            return msg.sender_id == user.id and msg.sender_deleted_at is None or \
                   msg.recipient_id == user.id and msg.recipient_deleted_at is None
            
        thread = root and list(traverse(root)) or ()
        thread = filter(not_deleted, thread)
        cache.set(cache_key, thread)
        return thread
    
    @classmethod
    def invalidate_cache(cls, sender, instance, created, *args, **kw):
        cache.delete("conversation_thread_%s" % instance.pk)
        key1 = cache.Key("conversation_unread_counter", instance.sender_id)
        key2 = cache.Key("conversation_unread_counter", instance.recipient_id)
        cache.delete(key1)
        cache.delete(key2)
    
    def is_read(self):
        assert self.user
        if self.user == self.sender:
            return not bool(self.sender_unread_cnt)
        else:
            return not bool(self.recipient_unread_cnt)
    
    def mark_read(self):
        assert self.user
        if self.user == self.sender:
            self.sender_unread_cnt = 0
        if self.user == self.recipient:
            self.recipient_unread_cnt = 0
            
    def cnt(self):
        assert self.user
        return self.sender_cnt if self.user == self.sender else self.recipient_cnt

    @models.permalink
    def get_absolute_url(self):
        return ('messages_view_conversation', [self.id])
        
signals.post_save.connect(Conversation.invalidate_cache, sender=Conversation)

class LazyUnreadCnt(object):
    def __get__(self, user, obj_type=None):
        if user.is_authenticated():
            if not hasattr(user, '_unread_cnt'):
                user._unread_cnt = Conversation.objects.unread_counter(user)
            return user._unread_cnt

User.add_to_class('unread_conversation_counter', LazyUnreadCnt())

# fallback for email notification if django-notification could not be found
try:
    notification = get_app('notification')
except ImproperlyConfigured:
    notification = None
    from messages.utils import new_message_email
    signals.post_save.connect(new_message_email, sender=Message)

def inbox_count_for(user):
    """
    returns the number of unread messages for the given user but does not
    mark them seen
    """
    return Message.objects.filter(recipient=user, read_at__isnull=True, recipient_deleted_at__isnull=True).count()
