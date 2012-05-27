from api.tests.utils import ApiTestCase
from django.utils import simplejson as json
import logging
logger = logging.getLogger(__name__)

MSG_KEYS = ('resource_uri', 'recipient_uri', 'sender_uri', 'subject', 'body',
            'date', 'read_at', 'parent_uri')

class MsgTest(ApiTestCase):
  
    def test_msg(self):
        status, data = self.get("/profile/messages/")
        self.assertEquals(status, 401)
        
        status, data = self.get("/profile/messages/inbox/", 'test')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(len(data['objects']),0)

        status, data = self.get("/profile/messages/outbox/", 'test')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(len(data['objects']),0)

        status, data = self.get("/profile/messages/trash/", 'test')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(len(data['objects']),0)
        
        # msg to self
        msg = dict(
           subject = 'msg subject',
           body = 'msg body',
           recipient_uri = self.API_BASE + '/user/test/',
        )

        status, data = self.post('/profile/messages/', msg, 'test')
        self.assertEquals(status, 200)
        resource_uri = data['resource_uri']

        status, data = self.get('/profile/messages/inbox/', 'test')
        logger.info(data)
        self.assertEquals(len(data['objects']), 1)

        status, data = self.get('/profile/messages/outbox/', 'test')
        self.assertEquals(len(data['objects']), 1)
        
        status, data = self.delete(resource_uri, 'test')
        self.assertEquals(status, 200)
        
        status, data = self.get('/profile/messages/trash/', 'test')
        self.assertPaginatedCollection(data)
        self.assertEquals(len(data['objects']), 1)

    def test_conversation(self):
        msg = dict(
            subject = 'conv test',
            body = 'conv test',
            recipient_uri = self.API_BASE + '/user/bob/',
        )
        status, msg1 = self.post('/profile/messages/', msg, 'alice')
        self.assertEquals(status, 200)
        logger.info(msg1)
        
        msg['recipient_uri'] = self.API_BASE + '/user/alice/'        
        msg['parent_uri'] = msg1['resource_uri']
        status, msg2 = self.post('/profile/messages/', msg, 'bob')
        logger.info(msg2)
        self.assertEquals(status, 200)

        msg['parent_uri'] = msg2['resource_uri']
        msg['recipient_uri'] = self.API_BASE + '/user/bob/'
        status, msg3 = self.post('/profile/messages/', msg, 'alice')
        logger.info(msg3)

        status, conversations = self.get('/profile/conversations/', 'alice')
        logger.info(conversations)
        self.assertEquals(len(conversations['objects']), 1)
        # alice didn't read 1 message from bob
        self.assertEquals(conversations['objects'][0]['message_cnt'], 3)
        self.assertEquals(conversations['objects'][0]['unread_cnt'], 1)

        status, messages = self.get(conversations['objects'][0]['messages_uri'], 'alice')
        self.assertEquals(len(messages['objects']), 3)
        self.assertEquals(sum(not m['is_read'] for m in messages['objects']), 1)
        
        logger.info(messages)
        for msg in messages['objects']:
            self.get(msg['resource_uri'], 'alice')

        status, conversations = self.get('/profile/conversations/', 'alice')
        self.assertEquals(conversations['objects'][0]['unread_cnt'], 0)
        
        status, response = self.delete(conversations['objects'][0]['resource_uri'], 'alice')
        self.assertEquals(status, 200)
        
        status, conversations = self.get('/profile/conversations/', 'alice')
        self.assertFalse(conversations['objects'])
        
        status, conversations = self.get('/profile/conversations/', 'bob')
        self.assertEquals(len(conversations['objects']), 1)

        # bob didn't read 2 messages from alice
        self.assertEquals(conversations['objects'][0]['unread_cnt'], 2)
        for msg in conversations['objects']:
            self.delete(msg['resource_uri'], 'bob')
        
        status, conversations = self.get('/profile/conversations/', 'bob')
        self.assertFalse(conversations['objects'])
        