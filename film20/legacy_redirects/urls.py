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
from django.shortcuts import redirect
from film20.legacy_redirects.views import *
from film20.blog.models import *

legacyredirectspatterns = patterns('',
    (r'^'+urls['SHOW_PROFILE']+'/(?P<username>[\w\-_]+)/'+urls['BLOG_POST_OLD']+'/(?P<permalink>[\w\-_]+)/$',
        redirect_to_blog_post),
    (r'^'+urls["FILM"]+'/(?P<permalink>[\w\-_]+)/'+urls["SHORT_REVIEW_OLD"]+'-(?P<username>[\w\-_]+)/$', redirect_to_short_review),
    (r'^wff/$', redirect_to_wff),
    (r'^aff/$', redirect_to_aff),
    (r'^sputnik/$', redirect_to_sputnik),
    (r'^piec-smakow/$', redirect_to_piec_smakow),
    (r'^offcamera/$', redirect_to_offcamera),
    (r'^filmy-swiata/$', redirect_to_filmy_swiata),
    (r'^filmyswiata/$', redirect_to_filmy_swiata),
    (r'^festiwal/filmyswiata/$', redirect_to_filmy_swiata),
    (r'^tofifest/$', redirect_to_tofifest),
    (r'^raindance/$', redirect_to_raindance),
    (r'^lff/$', redirect_to_lff),
)
