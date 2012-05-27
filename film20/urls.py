#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
from django.conf.urls.defaults import *

#from django.contrib.comments.models import FreeComment
from film20.config.urls import *
from film20.account.urls import *
from film20.core.urls import *
from film20.blog.urls import *
from film20.filmbasket.urls import *
from film20.regional_info.urls import *

from film20.recommendations.urls import *
from film20.event.urls import *
from film20.contest.urls import *
from film20.import_films.urls import *
from film20.externallink.urls import *
from film20.moderation.urls import urlpatterns as moderationpatterns
from film20.merging_tools.urls import urlpatterns as mergingtoolspatterns
from film20.add_films.urls import urlpatterns as addfilmspatterns
from film20.demots.urls import urlpatterns as demotspatterns
from film20.followers.urls import *
from film20.search.urls import *
from film20.posters.urls import *
from film20.register.urls import *
from film20.sitemap import sitemappatterns
from film20.dashboard.urls import *
from film20.legacy_redirects.urls import *
from film20.threadedcomments.urls import urlpatterns as threadedcommentspatterns
from film20.messages.urls import urlpatterns as messagespatterns
from film20.upload.urls import urlpatterns as uploadpatterns
from film20.facebook_connect.urls import root_urlpatterns as fbpatterns
from film20.useractivity.urls import urlpatterns as activity_patterns

from django.conf import settings
LOCAL = settings.LOCAL
from django.views.generic.list_detail import object_list
from django.contrib import admin

from django import template
template.add_to_builtins('film20.core.templatetags.utils')

from filebrowser.sites import site as filebrowser_site

admin.autodiscover()

urlpatterns = patterns('',

    # rejestracja: TODO: przeniesc
#    (r'^', include('film20.userprofile.urls')),

    # Uncomment this for admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/filebrowser/', include(filebrowser_site.urls)),

    (r'^fb/', include('film20.facebook_connect.urls')),
    (r'^ping/$', 'film20.core.views.ping'),
    (r'^fbapp/', include('film20.fbapp.urls')),
    url(r'^%(SETTINGS)s/' % urls, include('film20.usersettings.urls')),
    url(r'^%(PW)s/' % urls, include('film20.messages.urls')),
    url(r'^%(SHOWTIMES)s/' % urls, include('film20.showtimes.urls')),
    url(r'^%(SHOW_FESTIVAL)s/(?P<permalink>[\w\-_]+)/' % urls, include('film20.festivals.urls')),
    url(r'^%(SHOW_PROFILE)s/(?P<username>[\w\-_]+)/' % urls, include('film20.publicprofile.urls')),
    url(r'^vue/', include('film20.vue.urls')),
    # TODO: is this necessary ??
    url(r'^(?P<content_type>\d+)/(?P<object_id>\d+)/$', 'film20.threadedcomments.views.comment', name="tc_comment"),
)

# account
urlpatterns += accountpatterns 

# core
urlpatterns += corepatterns 

urlpatterns += legacyredirectspatterns

urlpatterns += fbpatterns
urlpatterns += recompatterns
urlpatterns += filmbasketpatterns
urlpatterns += eventpatterns
urlpatterns += contestpatterns
urlpatterns += importfilmspatterns
urlpatterns += externallinkpatterns
urlpatterns += regionalinfopatterns
urlpatterns += sitemappatterns
urlpatterns += followpatterns
urlpatterns += searchpatterns
urlpatterns += posterpatterns
urlpatterns += moderationpatterns
urlpatterns += mergingtoolspatterns
urlpatterns += registerpatterns
urlpatterns += addfilmspatterns
urlpatterns += dashboardpatterns
urlpatterns += threadedcommentspatterns
urlpatterns += uploadpatterns
urlpatterns += activity_patterns
urlpatterns += demotspatterns

never_cache(admin.site.urls)

if LOCAL:
    import os
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(BASE_DIR,'static')}),
    )

js_info_dict = {
    'packages': (),
}

urlpatterns += patterns('',
    #(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'^jsi18n/((?P<packages>\S+?)/)?$', 'django.views.i18n.javascript_catalog'),
)

urlpatterns += patterns('',
  url('^oauth/', include('film20.api.oauth_urls')),
)

urlpatterns += patterns('',
  url(r'^view-sql/(?P<key>.*)/$', 'film20.utils.sql.view_sql', name='view_sql'),
)

from film20.api.urls import urlpatterns as api_patterns
urlpatterns += patterns('',
  url(r'^api/', include(api_patterns)),
)

urlpatterns += patterns('',
  url('^account/logout/$', 'film20.account.views.logout'),
)

try:
  import film20.local
  urlpatterns += film20.local.urlpatterns
except:
  pass

handler500 = 'film20.core.views.handler500'
handler404 = 'film20.core.views.handler404'
