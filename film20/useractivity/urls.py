from django.conf.urls.defaults import *

urlpatterns = patterns('film20.useractivity.views',
    url(r'^action/activity/subscribe/$', 'subscribe'),
    url(r'^ajax/activity/remove/(?P<id>\d+)/$', 'remove', name='activity-remove'),
)

