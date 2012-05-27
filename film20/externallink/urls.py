from django.conf.urls.defaults import *
from film20.config.urls import *

from film20.externallink.views import *

externallinkpatterns = patterns('',
    url(r'^'+urls["FILM"]+'/(?P<permalink>[\w\-_]+)/'+urls["ADD_LINKS"]+'/$', add_link),
    url(r'^'+urls["FILM"]+'/(?P<permalink>[\w\-_]+)/'+urls["ADD_VIDEO"]+'/$', add_video, name="add-video"),
    url(r'^'+urls["FILM"]+'/(?P<permalink>[\w\-_]+)/'+urls["ADD_LINKS"]+'/(?P<ajax>json|xml)/$', add_link,),
    url(r'^'+urls["FILM"]+'/(?P<permalink>[\w\-_]+)/'+urls["REMOVE_LINKS"]+'/(?P<id>\d{1,8})/$', remove_link),
    url(r'^remove_video/(?P<id>\d+)/$', remove_video, name='remove-video'),
    url(r'^partial_link/(?P<link_id>\d+)/$', link_partial),
)
