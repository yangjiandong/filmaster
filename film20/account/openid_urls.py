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
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django_openidauth.regviews import register
from film20.config.urls import *
from django.shortcuts import render_to_response as render

def if_not_user_url(request):
    return HttpResponseRedirect(reverse('acct_login'))

def openid_login_failure(request, message):
    return render('account/login.html', {
        'message': message
    })

def openid_register(request, url):
    from film20.account.views import openid_new_user
    return openid_new_user(request)

def openid_login_succ(request,url):
    return HttpResponseRedirect(request.GET.get('next') or '/')

urlpatterns = patterns('',
    url(r'^login/$', 'django_openidconsumer.views.begin', {
        'sreg': 'email,nickname',
        'redirect_to': '/openid/complete/',
        'if_not_user_url': if_not_user_url,
        'on_failure':openid_login_failure
    }, name="openid_login"),
    url(r'^complete/$', 'django_openidauth.views.complete', {
        'on_login_ok': openid_login_succ,
        'on_login_failed': openid_register,
    }, name="openid_complete"),
    url(r'^logout/$', 'django_openidconsumer.views.signout', name="openid_logout"),
    url(r'^associations/$', 'django_openidauth.views.associations', {
        'template_name': 'openid/associations.html',
    }, name="openid_assoc"),
    url(r'assign-openid/$', 'film20.account.views.openid_assign', name='openid_assign'),
)
