from django.conf.urls.defaults import *
from film20.config.urls import urls

urlpatterns = patterns('film20.merging_tools.views',
    url( r'^%(MODERATION)s/admin/merging/people/$' % urls, 'people_merging', name='people-merging-tool' ),
    url( r'^%(MODERATION)s/admin/merging/people/resolve/(?P<id>\d+)/$' % urls, 'people_merging_resolve', name='people-merging-tool-resolve' ),
    url( r'^%(MODERATION)s/admin/merging/person/request/$' % urls, 'request_duplicate', { 'type': 'person' }, name='request-duplicate-person' ),

    url( r'^%(MODERATION)s/admin/merging/movies/$' % urls, 'film_merging', name='movie-merging-tool' ),
    url( r'^%(MODERATION)s/admin/merging/movies/resolve/(?P<id>\d+)/$' % urls, 'film_merging_resolve', name='movie-merging-tool-resolve' ),
    url( r'^%(MODERATION)s/admin/merging/movies/request/$' % urls, 'request_duplicate', { 'type': 'film' }, name='request-duplicate-movie' ),
)
