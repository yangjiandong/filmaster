from django.conf.urls.defaults import *
handler404 = 'film20.api.views.handler404'

urlpatterns = patterns('',
    url('^saas/1.0/', include('film20.api.saas.urls')),
    url('^1.1/', include('film20.api.api_1_1.urls')),
    url('^1.0/', include('film20.api.api_1_0.urls')),
)
