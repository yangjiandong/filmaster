from django.http import HttpResponse, Http404
from django.template import loader
from django.core import urlresolvers, paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.conf.urls.defaults import *
from django.utils.encoding import smart_str
from django.contrib.sitemaps.views import index, sitemap
from django.views.decorators.cache import cache_page
from django.conf import settings

from film20.core.models import Object
from film20.useractivity.models import UserActivity

from film20.sitemap import LimitSitemap

class ActivitySitemap(LimitSitemap):
    priority = 0.4
    changefreq = 'hourly'
    def items(self):
        return UserActivity.objects.public().filter(
                    subdomain=self.subdomain,
                    activity_type__in = [UserActivity.TYPE_POST, UserActivity.TYPE_SHORT_REVIEW]
               )

sitemaps = {
        'activities': ActivitySitemap,
}

@cache_page(settings.CACHE_SITEMAP_SUBDOMAIN_HOURS * 3600)
def subdomain_index(request, username, sitemaps):
    return index(request, sitemaps)

@cache_page(settings.CACHE_SITEMAP_SUBDOMAIN_HOURS * 3600)
def subdomain_sitemap(request, username, section, sitemaps):
    return sitemap(request, sitemaps)

sitemappatterns = patterns('',
    (r'^sitemap.xml$', subdomain_index, {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', subdomain_sitemap, {'sitemaps': sitemaps}),
)

