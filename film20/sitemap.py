from django.conf.urls.defaults import *
from django.views.decorators.cache import cache_page

# sitemaps
from django.contrib.sitemaps import FlatPageSitemap, GenericSitemap, Sitemap
from film20.core.models import Film, Person
from film20.useractivity.models import UserActivity
from film20.utils import cache
from django.core.paginator import Page
from django.conf import settings

class SitemapPaginator(object):
    def __init__(self, queryset, page_size):
        self.queryset = queryset.order_by('id')
        key = cache.Key("sitemap_paginator", str(self.queryset.query))
        self.ids = cache.get(key)
        if self.ids is None:
            self.ids = list(self.queryset.values_list('id', flat=True))[::page_size]
            cache.set(key, self.ids)
        self.num_pages = len(self.ids)
    
    def page(self, n):
        try:
            n = int(n)
        except ValueError, e:
            n = 1
        items = self.queryset.filter(id__gte=self.ids[n-1])
        if n < self.num_pages:
            items = items.filter(id__lt=self.ids[n])
        return Page(items, n, self)

class LimitSitemap(Sitemap):
    # Thanks Oduvan for that tip :>
    # http://stackoverflow.com/questions/2079786/caching-sitemaps-in-django/2527519#2527519
    limit = 2000
    date_field = None

    def _paginator(self):
        return SitemapPaginator(self.items(), self.limit) 
    paginator = property(_paginator)

    @property
    def subdomain(self):
        request = getattr(self, 'request', None)
        site = getattr(self, 'site', None)
        sub = request and getattr(request, 'subdomain', None) or site and site.domain.split('.')[0]
        assert sub
        return sub


    def get_urls(self, page=1, site=None):
        urls = []
        self.site = site
        for item in self.paginator.page(page).object_list:
            loc = self.location(item)
            if loc.startswith('/'):
                loc = (site and site.domain or settings.FULL_DOMAIN) + loc
            priority = self.priority
            url_info = {
                'location':   loc,
                'lastmod':    self.lastmod(item),
                'changefreq': self.changefreq,
                'priority':   str(priority is not None and priority or '')
            }
            urls.append(url_info)
        return urls
    
    def lastmod(self, item):
        if self.date_field is not None:
            return getattr(item, self.date_field)
        return None

class FilmsSitemap(LimitSitemap):
    priority = 0.6
    changefreq = 'weekly'
    def items(self):
        return Film.objects.all()

class PersonsSitemap(LimitSitemap):
    priority = 0.5
    changefreq = 'weekly'
    def items(self):
        return Person.objects.all()


sitemaps = {
    'flatpages': FlatPageSitemap,
    'films': FilmsSitemap,
    'persons': PersonsSitemap,
}

from django.contrib.sitemaps.views import index, sitemap

index = cache_page(settings.CACHE_SITEMAP_HOURS * 3600)(index)
sitemap = cache_page(settings.CACHE_SITEMAP_HOURS * 3600)(sitemap)

sitemappatterns = patterns('',
    (r'^sitemap.xml$', index, {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', sitemap, {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
)

