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
from django.utils.text import wrap
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.template import Context, loader
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import get_app
from django.core.exceptions import ImproperlyConfigured

# favour django-mailer but fall back to django.core.mail
try:
    mailer = get_app("mailer")
    from mailer import send_mail
except ImproperlyConfigured:
    from django.core.mail import send_mail

def format_quote(text):
    """
    Wraps text at 55 chars and prepends each
    line with `> `.
    Used for quoting messages in replies.
    """
    lines = wrap(text, 55).split('\n')
    for i, line in enumerate(lines):
        lines[i] = "> %s" % line
    return '\n'.join(lines)
    
def new_message_email(sender, instance, signal, 
        subject_prefix=_(u'New Message: %(subject)s'),
        template_name="messages/new_message.html", *args, **kwargs):
    """
    This function sends an email and is called via Django's signal framework.
    Optional arguments:
        ``template_name``: the template to use
        ``subject_prefix``: prefix for the email subject.
    """

    if 'created' in kwargs and kwargs['created']:
        try:
            current_domain = Site.objects.get_current().domain
            subject = subject_prefix % {'subject': instance.subject}
            message = render_to_string(template_name, {
                'site_url': 'http://%s' % current_domain,
                'message': instance,
            })
            if instance.recipient.email != "":
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                    [instance.recipient.email,])
        except Exception, e:
            #print e
            pass #fail silently
