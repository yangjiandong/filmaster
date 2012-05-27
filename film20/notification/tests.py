# -!- coding: utf-8 -!-
from film20.utils.test import TestCase
from film20.notification.models import send, create_notice_type
from django.contrib.auth.models import User
from django.core import mail

import logging
logger = logging.getLogger(__name__)

class S(object):
    """ helper class for non-string tag input tests"""
    def __init__(self, v):
        self.v = v
    def __unicode__(self):
        return self.v
        
class Test(TestCase):

    def test_notice(self):
        create_notice_type("test_notice", "Test Notice", "test notice", default=2)
        user, _ = User.objects.get_or_create(username='test', defaults=dict(email='test@test.pl'))
        send([user], 'test_notice')
        self.assertTrue(any('Test Notice' in m.subject for m in mail.outbox))

    def test_apns(self):
        from .apns import iPhonePush
        from .models import NoticeType
        import APNSWrapper

        class FakeAPNSNotificationWrapper(object):
            def __init__(self, *args, **kw):
                pass
            def notify(self): pass
            def append(self, *args): pass
        APNSWrapper.APNSNotificationWrapper = FakeAPNSNotificationWrapper
        
        user, _ = User.objects.get_or_create(username='test', defaults=dict(email='test@test.pl'))
        p = user.get_profile()
        import base64
        p.iphone_token = base64.standard_b64encode('1' * 16)
        p.save()
        type = NoticeType.objects.get(label='messages_reply_received')
        medium = iPhonePush()
        from django.template import Context
        class o(object):
            def __init__(self, **kw):
                self.__dict__.update(kw)
        message = o(
            pk=9998,
            parent_msg=o(pk=9999),
            conversation_id="999",
            sender=o(username="username"*4),
            body=u"very long body. " * 10)
        
        medium.send_notice_impl(user, type, Context(dict(message=message)))

from django.template import Template, Context
from .templatetags.notification import render_template

class TestTags(TestCase):

    def test_autocut(self):
        template = Template(u"{%load notification%}xyz {{val1|autocut1:ctx}}{{val2|autocut2:ctx}}")
        ctx = Context(dict(
            val1 = S("ab" * 5),
            val2 = S("cd" * 5),
        ))
        
        out = render_template(template, ctx)
        self.assertEquals(out, "xyz abababababcdcdcdcdcd")

        out = render_template(template, ctx, 20)
        self.assertEquals(out, "xyz aba...cdcdcdcdcd")

        out = render_template(template, ctx, 10)
        self.assertEquals(out, "xyz cdc...")
        
        ctx['val2'] = u"aąćęółńśźż"
        out = render_template(template, ctx, 10)
        self.assertEquals(out, u"xyz ...")

    def test_short_url(self):
        template = Template(u"{%load notification%}{{url|short_url}}")
        ctx = Context()
        ctx['url'] = S('http://filmaster.pl/' + 'foo/' * 20)
        out = render_template(template, ctx)
        logger.info(out)
        # http://bit.ly/1234567890 - len:24
        self.assertTrue(len(out) < 30)
        
        template = Template(u"{%load notification%}{%filter short_urls%}{{url}} {{url}}{%endfilter%}")
        out = render_template(template, ctx)
        logger.info(out)
        self.assertTrue(len(out) < 60)

        template = Template(u"""{%load notification%}{%with url|short_url as url%}{{url}}{%endwith%}""")
        template.render(ctx)
