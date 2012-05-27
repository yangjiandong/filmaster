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
from film20.utils.test import TestCase
from django.contrib.auth.models import User
from film20.messages.models import Message, Conversation

class SendTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('user1', 'user1@example.com', '123456')
        self.user2 = User.objects.create_user('user2', 'user2@example.com', '123456')
        self.msg1 = Message(sender=self.user1, recipient=self.user2, subject='Subject Text', body='Body Text')
        self.msg1.save()
        
    def testBasic(self):
        self.assertEquals(self.msg1.sender, self.user1)
        self.assertEquals(self.msg1.recipient, self.user2)
        self.assertEquals(self.msg1.subject, 'Subject Text')
        self.assertEquals(self.msg1.body, 'Body Text')
        self.assertEquals(self.user1.sent_messages.count(), 1)
        self.assertEquals(self.user1.received_messages.count(), 0)
        self.assertEquals(self.user2.received_messages.count(), 1)
        self.assertEquals(self.user2.sent_messages.count(), 0)

        msg = Message.objects.get(id=self.msg1.id)
        
        self.assertEquals(msg.conversation.body, msg.body)
        self.assertEquals(msg.conversation.subject, msg.subject)
        self.assertEquals(msg.conversation.sender_cnt, 1)
        self.assertEquals(msg.conversation.recipient_cnt, 1)

        self.msg2 = Message(sender=self.user2, recipient=self.user1, subject='sub2', body='body2', parent_msg = self.msg1)
        self.msg2.save()
        
        msg2 = Message.objects.get(id=self.msg2.id)
        
        self.assertEquals(msg2.conversation, msg.conversation)
        
        self.assertEquals(msg2.conversation.body, msg2.body)
        self.assertEquals(msg2.conversation.subject, msg2.subject)
        self.assertEquals(msg2.conversation.sender_cnt, 2)
        self.assertEquals(msg2.conversation.recipient_cnt, 2)
        
class DeleteTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user('user3', 'user3@example.com', '123456')
        self.user2 = User.objects.create_user('user4', 'user4@example.com', '123456')
        self.msg1 = Message(sender=self.user1, recipient=self.user2, subject='Subject Text 1', body='Body Text 1')
        self.msg1.save()
        self.msg2 = Message(sender=self.user1, recipient=self.user2, subject='Subject Text 2', body='Body Text 2')
        self.msg2.save()
        self.msg3 = Message(sender=self.user2, recipient=self.user1, subject='s', parent_msg=self.msg2)
        self.msg3.save()
                
    def testBasic(self):
        self.assertEquals(Message.objects.outbox_for(self.user1).count(), 2)
        self.assertEquals(Message.objects.inbox_for(self.user2).count(), 2)
        self.msg1.delete_by(self.user1)

        self.msg2.delete_by(self.user2)
        
        self.assertEquals(Message.objects.outbox_for(self.user1).count(), 1)
        self.assertEquals(Message.objects.outbox_for(self.user1).all()[0].subject, 'Subject Text 2')
        self.assertEquals(Message.objects.inbox_for(self.user2).count(), 1)
        self.assertEquals(Message.objects.inbox_for(self.user2).all()[0].subject, 'Subject Text 1')
        
        c = Conversation.objects.get(id=self.msg3.conversation.id)
        self.assertEquals(c.messages.count(), 2)
        self.assertEquals(c.user_messages(self.user1).count(), 2)
        self.assertEquals(c.user_messages(self.user2).count(), 1)
        
                
