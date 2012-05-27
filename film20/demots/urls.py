from django.conf.urls.defaults import *
from film20.config.urls import urls

urlpatterns = patterns('film20.demots.views',
    url( r'^%(DEMOTS)s/$' % urls, 'demots', name='demots' ),
    url( r'^%(DEMOTS_ADD)s/$' % urls, 'add_demot', name='add-demot' ),
    url( r'^%(DEMOT)s/delete/(?P<pk>\d+)/$' % urls, 'remove_demot', name='remove-demot' ),
)
