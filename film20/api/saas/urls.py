from django.conf.urls.defaults import *
from .handlers import *
handler404 = 'film20.api.views.handler404'

urlpatterns = patterns('',
    url('^user/$', users_handler),
    url('^user/(?P<id>.*)/ratings/$', user_ratings_handler),
    url('^user/(?P<id>.*)/recommendations/similar/$', user_recommendations_handler),
    url('^user/(?P<id>.*)/$', users_handler),
    url('^film/imdb/(?P<imdb_code>.*)/$', films_handler),
    url('^ratings/', ratings_handler),
)
