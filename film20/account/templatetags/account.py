from django.utils.translation import gettext as _
from django import template
from film20.account.models import OAUTH_SERVICES
from urllib import urlencode
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings
import cgi
import logging
logger = logging.getLogger(__name__)

register = template.Library()

def get_next(request):
    login_url = settings.FULL_DOMAIN + reverse('acct_login')
    index_url = settings.FULL_DOMAIN + '/'
    logout_url = settings.FULL_DOMAIN + reverse('acct_logout')
    
    params = [i for i in cgi.parse_qsl(request.META.get('QUERY_STRING', ''), keep_blank_values=0) if i[0] != 'next']
    next = request.REQUEST.get('next', '')
    if not next:
        from film20.utils.utils import is_ajax
        next = 'http://' + request.get_host() + request.get_full_path()
        if is_ajax(request) or 'iframe' in request.GET:
            next = request.META.get('HTTP_REFERER', '')
        spath = next.split('?')[0]
        if spath in (login_url, index_url, logout_url):
            return ''
    else:
        if next.startswith('/'):
            next = 'http://' + request.get_host() + next
    params.append(('next', next))
    return mark_safe(urlencode(params))

register.simple_tag(get_next)

@register.simple_tag
def oauth_buttons(request):
    out = []
    for service in OAUTH_SERVICES:
        next = get_next(request)
        ctx = dict(
            name = service.normalized_name,
            url = settings.FULL_DOMAIN + reverse('oauth_login', args=[service.normalized_name]) + '?' + next,
        )
        out.append("<a href='%(url)s' class='%(name)s-button'>%(name)s</a>" % ctx)
    return mark_safe(u''.join(out))

@register.inclusion_tag('account/ajax_signup.html', takes_context=True)
def signup_form(context):
    from film20.account.forms import SignupForm
    from film20.account.models import OAUTH_SERVICES

    request = context['request']
    form = SignupForm(None, request=request, prefix='ajax')
    return {
        'form':form,
        'request':request,
        'form_class': 'ajax',
        'settings': settings,
        'OAUTH_SERVICES': OAUTH_SERVICES,
    }


