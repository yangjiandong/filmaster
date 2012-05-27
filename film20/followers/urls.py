from django.conf.urls.defaults import *
from film20.followers.views import *
from film20.config.urls import *

followpatterns = patterns('',
    url(r'^'+urls['FOLLOW']+'/$', follow, name="follow_widget"),
    (r'^'+urls['FOLLOW']+'/(?P<ajax>json|xml)/$', follow),
    (r'^follow_partial/(?P<user_id>[\d]+)/$', follower_partial),
    )
