from django.core.urlresolvers import reverse as django_reverse
from django.conf import settings

from film20.config.urls import urls

import re

PREFIX_RE  = re.compile(r'^/%(SHOW_PROFILE)s/([\w\-_0-9]+)/' % urls)
FULLURL_RE = re.compile('(https?://)(.*)')

def make_absolute_url(path, secure=False):
    fullurl = FULLURL_RE.match(path)
    if fullurl:
        path = fullurl.group(2)
        return (secure and "https://" or "http://") + path
    domain = settings.DOMAIN
    if settings.SUBDOMAIN_AUTHORS:
        match = PREFIX_RE.match(path)
        if match:
            path = path[len(match.group(0))-1:]
            domain = match.group(1).lower() + '.' + settings.DOMAIN

    return (secure and "https://" or "http://") + domain + path

def get_url_path(url):
    if url.startswith(settings.FULL_DOMAIN):
        return url[len(settings.FULL_DOMAIN):]
    return url

def reverse(*args, **kw):
    """
    hacked version of reverse returning absolute urls with author subdomains when necessary
    """
    return make_absolute_url(django_reverse(*args, **kw))
