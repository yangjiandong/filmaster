from django.conf.urls.defaults import *
from film20.config.urls import urls
from django.views.generic.simple import redirect_to  

urlpatterns = patterns('film20.showtimes.views',
#    url(r'^$', redirect_to, {'url': '/%(SHOWTIMES)s/%(THEATERS)s/' % urls}, name='recommendations'),
    url(r'^%(THEATERS)s/$' % urls, 'showtimes', name='recommendations_theaters'),
    url(r'^%(TV)s/$' % urls, 'showtimes_tv', name='recommendations_tv'),
    url(r'^%(TV)s/(?P<date>\d\d\d\d-\d\d-\d\d)/$' % urls, 'showtimes_tv_single_day', name='recommendations_tv'),
    url(r'^%(SCREENING)s/(?P<id>\d+)/' % urls, 'screening', name='showtimes_screening'),
    url(r'^%(CHANNEL)s/(?P<id>\d+)/' % urls, 'tvchannel', name='showtimes_tvchannel'),
    url(r'^%(THEATERS)s/(?P<id>\d+)/' % urls, 'theater', name='showtimes_theater'),
)
