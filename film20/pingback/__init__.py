# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)
from urlparse import urlsplit
from urllib2 import urlopen, HTTPError, URLError

from BeautifulSoup import BeautifulSoup

from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.core import urlresolvers
from django.conf import settings
from django.utils.html import strip_tags

from film20.pingback.models import Pingback
from film20.pingback.exceptions import PingbackError
from film20.pingback.client import ping_external_links, ping_directories

__all__ = ['Pingback', 'ping_external_links', 'ping_directories', 'ping_func',
           'register_pingback']

def register_pingback(view, pingback_func):
    '''Register a pingback on a view function

    Pingback function should accept same arguments as a view (excluding
    request) and return single Model object.

    Example code::

        def post_pingback(slug, **kwargs):
            return Post.objects.get(slug=slug)
        register_pingback('blog.views.post_detail', post_pingback)
    '''
    if isinstance(view, basestring):
        mod, view = view.rsplit('.', 1)
        mod = __import__(mod, fromlist=True)
        view = getattr(mod, view)
    view.pingback = pingback_func

def ping_func(source, target):
    """
    pingback.ping is a method for notifying server of incoming links.

    For blogging software, etc. Allows for an XML-RPC client to notify
    of an incoming link. If the link target is pingable and linking page
    is correct, the link is stored and will be usable on web pages.
    """

    log = logging.getLogger('pingback')
    log.debug('received pingback from %r to %r' % (source, target))
    domain = Site.objects.get_current().domain

    # fetch the source request, then check if it really pings the target.
    try:
        doc = urlopen(source)
    except (HTTPError, URLError):
        log.debug('source does not exist')
        return PingbackError.SOURCE_DOES_NOT_EXIST

    # does the source refer to the target?
    soup = BeautifulSoup(doc.read())
    mylink = soup.find('a', attrs={'href': target})
    if not mylink:
        log.debug('source has no reference to us')
        return PingbackError.SOURCE_DOES_NOT_LINK

    # grab the title of the pingback source
    title = soup.find('title')
    if title:
        title = strip_tags(unicode(title))
    else:
        title = 'Unknown title'

    # extract the text around the incoming link
    content = unicode(mylink.findParent())
    i = content.index(unicode(mylink))
    content = strip_tags(content)
    max_length = getattr(settings, 'PINGBACK_RESPONSE_LENGTH', 200)
    if len(content) > max_length:
        start = i - max_length/2
        if start < 0:
            start = 0
        end = i + len(unicode(mylink)) + max_length/2
        if end > len(content):
            end = len(content)
        content = content[start:end]

    scheme, server, path, query, fragment = urlsplit(target)

    # check if the target is valid target
    if domain not in [server, server.split(':')[0]]:
        log.debug('ping is directed to invalid target: %s' % server)
        return PingbackError.TARGET_IS_NOT_PINGABLE

    resolver = urlresolvers.get_resolver(None)
    try:
        func, a, kw = resolver.resolve(path)
    except urlresolvers.Resolver404:
        return PingbackError.TARGET_DOES_NOT_EXIST

    # Check if view accept pingbacks
    try:
        obj = func.pingback(*a, **kw)
    except AttributeError:
        log.debug('this function does not accept pingbacks')
        return PingbackError.TARGET_IS_NOT_PINGABLE

    content_type = ContentType.objects.get_for_model(obj)
    try:
        Pingback.objects.get(url=source, content_type=content_type,
                             object_id=obj.id)
        log.debug('this pingback is already registered')
        return PingbackError.PINGBACK_ALREADY_REGISTERED
    except Pingback.DoesNotExist:
        pass

    pb = Pingback(object=obj, url=source, content=content.encode('utf-8'),
                  title=title.encode('utf-8'), approved=True)
    pb.save()
    log.debug('pingback successful')
    return 'pingback from %s to %s saved' % (source, target)

