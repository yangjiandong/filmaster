# favour django-mailer but fall back to django.core.mail
try:
    from mailer import send_mail
except ImportError:
    from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _, get_language, activate
from django.conf import settings
from django.utils import simplejson as json
from film20.facebook_connect.models import FBAssociation
import logging
logger = logging.getLogger(__name__)
from urllib2 import urlopen, HTTPError
from urllib import urlencode
import datetime, time
from threading import Condition, Thread
import re
from .templatetags.notification import render_template

class BaseMedium(object):
    NUMBER_OF_WORKERS = 1
    display = "base"
    name = "base"
    
    def should_send(self, user, notice_type):
        if self.supports(notice_type) and self.is_enabled(user):
            return self.get_notification_setting(user, notice_type).send

    def get_notification_setting(self, user, notice_type):
        from models import NoticeSetting
        default = (self.get_spam_sensitivity() <= notice_type.default)
        sett, created = NoticeSetting.objects.get_or_create(
                user=user,
                notice_type=notice_type,
                medium=self.id,
                defaults={'send': default}
        )
        return sett

    def update_notification_setting(self, user, notice_type, default):
        from models import NoticeSetting
        sett, created = NoticeSetting.objects.get_or_create(
                user=user,
                notice_type=notice_type,
                medium=self.id,
                defaults={'send': default}
        )
        if not created and sett.default != default:
            sett.default = default
            sett.save()
        return sett

    def description(self):
        return ''
    
    def supports(self, notice_type):
        return True
    
    def is_enabled(self, user):
        return True
        
    def send_notice(self, user, type, context, now=False):
        if getattr(settings, 'NOTIFICATION_QUEUE_ALL', False) and not now:
            from film20.core.deferred import defer
            key = '%s%s.notice.%s.%s' % (
                settings.CELERY_QUEUE_PREFIX, 
                settings.LANGUAGE_CODE, 
                self.name, 
                type.label
            )
            logger.debug('notice %r to %s queued to send via %s', type.label, user, self.name)
            defer(self._send_notice_impl, user, type, context, _routing_key=key)
        else:
            try:
                self._send_notice_impl(user, type, context)
            except Exception, e:
                pass

    def _send_notice_impl(self, user, type, context):
        from models import get_notification_language, LanguageStoreNotAvailable
        
        current_language = get_language()
        try:
            activate(get_notification_language(user))
        except LanguageStoreNotAvailable:
            pass
                
        logger.debug('sending %r to %s via %s', type.label, user, self.name)
        start = time.time()
        try:
            self.send_notice_impl(user, type, context)
            logger.debug('sent in %s seconds', time.time() - start)
        except Exception, e:
            logger.exception(e)
            raise

        activate(current_language)
        
    @classmethod
    def render_template(cls, type, names, context, max_len=None):
        if isinstance(names, basestring):
            names = (names, )
        context.autoescape = not names[0].endswith(".txt")
        paths = []
        for name in names:
            paths.extend((
                'notification/%s/%s' % (type.label, name),
                'notification/%s' % name
            ))

        ret = render_template(paths,
            context, 
            max_len)
        return ret.strip()

class Debug(BaseMedium):
    display = _("Debug")
    name = "debug"
    id = "debug"
    
    def send_notice_impl(self, user, type, context):
        message = self.render_template(type, 'full.txt', context)
        logger.debug("%r %r %r\n\n%s", user, type, context, message)

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 2

    
class EMail(BaseMedium):
    NUMBER_OF_WORKERS = 2
    display = _("Email")
    name = "email"
    id = "1"
    
    def is_enabled(self, user):
        return user.email
    
    def send_notice_impl(self, user, type, context):
        # Strip newlines from subject
        subject = ' '.join(render_to_string('notification/email_subject.txt', {
            'message': self.render_template(type, 'short.txt', context),
        }, context).splitlines())
        logger.debug("subject: %r", subject)

        # send html mail if full.html template exists
        from django.template import TemplateDoesNotExist
        try:
            message = self.render_template( type, 'full.html', context )
        except TemplateDoesNotExist:
            message = None

        if message:

            from email.MIMEImage import MIMEImage
            from BeautifulSoup import BeautifulSoup
            from django.core.mail import EmailMultiAlternatives

            body = render_to_string('notification/email_body.html', {
                'message': message,
            }, context)
            logger.debug("html body: %r", body)

            images = {}
            soup = BeautifulSoup( body )
            for index, tag in enumerate( soup.findAll( lambda t: t.name == u'img' ) ):
                src = tag['src']
                if not images.has_key( src ):
                    images[src] = 'img-%d' % index
                tag['src'] = "cid:%s" % images[src]

            msg = EmailMultiAlternatives( subject=subject, body=str( soup ),
                to=[user.email], from_email=settings.DEFAULT_FROM_EMAIL )
            
            for filename, file_id in images.items():
                try:
                    file = open( filename.replace( settings.MEDIA_URL, settings.MEDIA_ROOT ), 'rb' )
                    image= MIMEImage( file.read() )
                    image.add_header( 'Content-ID', '<%s>' % file_id )
                    msg.attach( image )
                    file.close()
                except Exception, e:
                    logger.error( 'problem with file: %s, SKIPPING' % filename, e ) 
            
            msg.content_subtype = "html"
            msg.send()
        
        else:
            body = render_to_string('notification/email_body.txt', {
                'message': self.render_template(type, 'full.txt', context),
            }, context)
            logger.debug("body: %r", body)

            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 2

FROM_JID = 'filmaster@xmpp-test.appspotchat.com'

class Jabber(BaseMedium):
    display = _("Jabber")
    name = "jabber"
    id = "3"
    
    def is_enabled(self, user):
        return user.get_profile().jabber_id
    
    def send_notice_impl(self, user, type, context):
        message = self.render_template(type, 'full.txt', context)
        jid = user.get_profile().jabber_id.encode('utf-8')
        data = urlencode(dict(
            msg=message.encode('utf-8'),
            jid=jid,
            from_jid=FROM_JID,
        ))
        urlopen('http://xmpp-test.appspot.com/proxy/', data).read()

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 2
    
    def description(self):
        return _("To receive jabber notifications set your JID in your profile and add <b>%s</b> to your roster") % FROM_JID

class Facebook(BaseMedium):
    display = _("Facebook")
    name = "facebook"
    id = "4"

    def is_enabled(self, user):
        assoc = user.get_profile().facebook_association
        return bool(assoc and assoc.access_token)
    
    def make_absolute(self, path):
        if path.startswith('/'):
            domain = settings.FULL_DOMAIN
            path = domain + path
        if path.startswith('http://localhost'):
            path = path.replace(settings.FULL_DOMAIN, 'http://filmaster.pl')
        return path
        
    def post(self, access_token, feed_url, type, context):
        description = self.render_template(type, 'facebook_description.txt', context).encode('utf-8')
        message = self.render_template(type, 'facebook_message.txt', context).encode('utf-8')
        data = dict(
            message=message,
            access_token=access_token,
            description=description,
        )

        for key in ('link', 'picture', 'icon'):
            if context.get(key):
                data[key] = self.make_absolute(context[key])

        try:
            reply = json.loads(urlopen(feed_url, urlencode(data)).read())
        except HTTPError, e:
            if e.code == 403:
                reply = {}
            else:
                raise
        return reply

    def send_notice_impl(self, user, type, context):
        assoc = user.get_profile().facebook_association
        if assoc and assoc.access_token:
            self.post(assoc.access_token, 'https://graph.facebook.com/me/feed', type, context)
        else:
            logger.warning("strange, no access_token?")

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 1
    
    def description(self):
        return _("To enable facebook notifications login with FBConnect")
        
    def supports(self, notice_type):
        return notice_type.type==notice_type.TYPE_USER_ACTIVITY

def shorten(url):
    params = dict(
        longUrl=url,
        login='mrkits',
        apiKey='R_03ac99e88a054d31f9c80e4b2dc71586',
    )
    try:
        resp = json.loads(urlopen('http://api.bitly.com/v3/shorten?' + urlencode(params)).read())
        url = resp['data']['url']
    except Exception, e:
        pass
    return url


class Twitter(BaseMedium):
    display = _("Twitter")
    name = "twitter"
    id = "twitter"
    
    URL_RE = re.compile(r"http://[\w.\-,\?/&=#%:]+")
    
    def is_enabled(self, user):
        return bool(user.get_profile().twitter_user_id)
    
    def send_notice_impl(self, user, type, context):
        from film20.account.models import OAuthService
        message = self.render_template(type, 'twitter.txt', context, 140)
        service = OAuthService.get_by_name("twitter")
        token = service.get_access_token(user)
        
        for url in set(self.URL_RE.findall(message)):
            message = message.replace(url, shorten(url))
        
        service.post(token, message)

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 1
    
    def description(self):
        return ""

    def supports(self, notice_type):
        return notice_type.type==notice_type.TYPE_USER_ACTIVITY

class Browser(BaseMedium):
    display = _("Browser")
    name = "Browser"
    id = "browser"
    
    def is_enabled(self, user):
        return True
    
    def send_notice_impl(self, user, type, context):
        message = self.render_template(type, 'full.txt', context)
        data = urlencode(dict(
            text=message.encode('utf-8'),
            client_id=user.username,
        ))
        urlopen('http://filmaster-tools.appspot.com/send/', data).read()

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 2
    
    def description(self):
        return '<a href="#" onclick="window.webkitNotifications.requestPermission(function(x){console.log(x);})">enable desktop notifications</a>'

