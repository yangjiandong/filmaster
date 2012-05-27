from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^request/token/$', 'piston.authentication.oauth_request_token'),
    url(r'^access/token/$', 'piston.authentication.oauth_access_token'),
    url(r'^authorize/$', 'film20.api.views.oauth_user_auth', name='oauth_authorize'),
    url(r'^authorize/(anon|fb)/$', 'film20.api.views.oauth_user_auth_anon', name='oauth_authorize_anon'),
)
