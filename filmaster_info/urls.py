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
from filmaster_info.register.views import *
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


from filmaster_info.settings import LOCAL

urlpatterns = patterns('',
    # Example:
    # (r'^filmaster_info/', include('filmaster_info.foo.urls')),
    (r'^$', register_email_view),
    (r'^rejestracja-testera/$', register_view),
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     (r'^admin/(.*)', admin.site.root),
)
if LOCAL:
    urlpatterns += patterns('',
     (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'c:/djcode/film20/filmaster_info/static'}),
    )
