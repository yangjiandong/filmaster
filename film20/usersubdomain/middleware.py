import re
import logging
logger = logging.getLogger(__name__)

from django.contrib.sites.models import Site
from django.http import Http404
from film20.core.middleware import SubdomainMiddleware

from django.contrib.auth.models import User
from film20.config.urls import urls
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import resolve, reverse
from django.conf import settings
from film20.config.urls import urls

VALID_SUBDOMAIN_PREFIXES = (
    settings.MEDIA_URL,
    '/api/',
    '/action/',
    '/jsi18n/',
    '/ajax/', 
    '/' + urls['REGISTRATION'] + '/',
)

class UserSubdomainMiddleware( SubdomainMiddleware ):
    def process_request( self, request ):
        super( UserSubdomainMiddleware, self ).process_request( request )

        if request.subdomain is not None:
            try:
                user = User.objects.get(username__iexact=request.subdomain, is_active=True)
                request.subdomain_user = user
                prefix = "/%s/%s" % (urls.get('SHOW_PROFILE'), request.subdomain)
                try:
                    resolve(prefix + request.path_info)
                    request.path_info = prefix + request.path_info
                except Http404, e:
                    if not any(request.path_info.startswith(p) for p in VALID_SUBDOMAIN_PREFIXES):
                        # dirty hack for old blog.filmaster.pl links
                        if request.subdomain == 'blog':
                            match = re.match( '/(?P<permalink>[\w\-_]+)/$', request.path_info )
                            if match:
                                return HttpResponseRedirect(
                                    reverse( 'show_article', args=[request.subdomain, match.group(1) ] ).replace( prefix, '' ) )
                        raise
            except User.DoesNotExist:
                logger.debug( 'User [ %s ] Does not exists ...' % request.subdomain )

    def process_response(self, request, response):
        if getattr(request, 'subdomain', None) is not None and not hasattr(request, 'subdomain_user'):
            import urls
            from django.core.urlresolvers import get_callable
            return get_callable(urls.handler404)(request)
        return super(UserSubdomainMiddleware, self).process_response(request, response)

# vim: fdm=marker ts=4 sw=4 sts=4
