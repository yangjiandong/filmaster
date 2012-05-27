import APNSWrapper as apns
from django.utils import simplejson as json
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import os
import logging
logger = logging.getLogger(__name__)

APNS_SANDBOX = getattr(settings, "APNS_SANDBOX", False)
APNS_SENDMAIL = getattr(settings, "APNS_SENDMAIL", ()) or ()
APNS_CERTIFICATE = getattr(settings, "APNS_CERTIFICATE", os.path.join(os.path.abspath(os.path.dirname(__file__)), "apns_cert.pem"))

class JSONProperty(apns.APNSProperty):
    def __init__(self, name, data, encoded=False):
        self.name = name
        self.data = data
        self.encoded = encoded
    
    def _build(self):
        return "%s:%s" % (json.dumps(self.name), self.data if self.encoded else json.dumps(self.data))

class APNSAlert(apns.APNSAlert):
    """ APNSAlert with unicode support """
    def __init__(self, body):
        super(APNSAlert, self).__init__()
        self.body(json.dumps(body)[1:-1])

from media import BaseMedium
class iPhonePush(BaseMedium):
    display = _("iPhone Push")
    name = "apns"
    id = "2"
    
    def is_enabled(self, user):
        token = user.get_profile().iphone_token
        try:
            return token and token.decode('base64')
        except Exception, e:
            logger.warning(unicode(e))
            return False
    
    def render_template(cls, type, names, context, max_len=None):
        context['cut_encoder'] = lambda s:json.dumps(s)[1:-1]
        context['cut_decoder'] = lambda s:json.loads('"%s"' % s)

        return super(iPhonePush, cls).render_template(type, names, context, max_len)

    def send_notice_impl(self, user, type, context):
        ALERT_TEMPLATES = ('apns_alert.txt', 'short.txt')
        data = self.render_template(type, 'data.json', context).encode('utf-8')
        alert = self.render_template(type, ALERT_TEMPLATES, context).encode('utf-8')
        badge = user.unread_conversation_counter

        def build_message(data, alert, badge):
            message = apns.APNSNotification()
            message.tokenBase64(user.get_profile().iphone_token)
            if badge is not None:
                message.badge(badge)
            if alert:
                alert = APNSAlert(alert)
                message.alert(alert)
            message.appendProperty(JSONProperty("type", type.label))
            message.appendProperty(JSONProperty("data", data, True))
            return message
        
        try:
            msg = build_message(data, alert, badge)
            msg.payload()
        except:
            try:
                # try without badge - few bytes extra
                msg = build_message(data, alert, None)
                msg.payload()
            except:
                if data != "{}":
                    # try to re-render data
                    msg = build_message("", alert, badge)
                    data_len = 256 - len(msg.payload())
                    data = self.render_template(type, 'data.json', context, data_len).encode('utf-8')
                    logger.debug("data_len: %d, cutted_len: %d", data_len, len(data))
                    msg = build_message(data, alert, badge)
                else:
                    # try to re-render alert str
                    msg = build_message(data, "x", badge)
                    print 'here !', repr(msg.payload()), len(msg.payload())
                    alert_len = 255 - len(msg.payload())
                    alert = self.render_template(type, ALERT_TEMPLATES, context, alert_len).encode('utf-8')
                    logger.debug("data_len: %d, cutted_len: %d", alert_len, len(alert))
                    msg = build_message(data, alert, badge)
                    print 'here !', repr(msg.payload()), len(msg.payload())
        try:
            if user.email in APNS_SENDMAIL:
                from media import send_mail
                send_mail("APSN message: %s" % type.label, msg._build(), settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception, e:
            logger.warning(unicode(e))

#        wrapper = apns.APNSNotificationWrapper(APNS_CERTIFICATE, APNS_SANDBOX, debug_ssl=False)
#        wrapper.append(msg)
#        wrapper.notify()

        logger.debug("apns message: %r succesfully sent to %s", msg._build(), user)

    # how spam-sensitive is the medium
    def get_spam_sensitivity(self):
        return 2

