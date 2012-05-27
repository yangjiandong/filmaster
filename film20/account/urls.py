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
from forms import *

from film20.config.urls import *

accountpatterns = patterns('',
    (r'^openid/', include('film20.account.openid_urls')),
    url(r'^email/$', 'film20.account.views.email', name="acct_email"),
    url(r'^'+urls['OAUTH_LOGIN']+'/(?P<name>.*)/$', 'film20.account.views.oauth_login', name='oauth_login'),
    url(r'^'+urls['OAUTH_LOGIN_CB']+'/(?P<name>.*)/$', 'film20.account.views.oauth_login_callback', name='oauth_login_callback'),
    url(r'^'+urls['OAUTH_NEW_USER']+'/(?P<name>.*)/$', 'film20.account.views.oauth_new_user', name='oauth_new_user'),
#    url(r'^'+urls['ASSOCIATIONS']+'/$', 'film20.account.views.associations', name="associations"),
    url(r'^'+urls['ASSOCIATIONS']+'/oauth-assoc/(?P<name>.*)/$', 'film20.account.views.oauth_associate', name='oauth_associate'),
    url(r'^'+urls['ASSOCIATIONS']+'/remove-assoc/(?P<name>.*)/$', 'film20.account.views.oauth_cancel', name='oauth_cancel'),
    url(r'^'+urls['ASSOCIATIONS']+'/oauth-cb/(?P<name>.*)/$', 'film20.account.views.oauth_assoc_callback', name='oauth_assoc_callback'),
            
#    url(r'^signup/$', 'film20.account.views.signup', name="acct_signup"),
    url(r'^'+urls['REGISTRATION']+'/$', 'film20.account.views.signup', name="acct_signup"),

    # just in case someone uses /login
    url(r'^login/$', 'film20.account.views.login', name="acct_login"),
    url(r'^'+urls['LOGIN']+'/$',
       'film20.account.views.login',
       name='acct_login'),

#    url(r'^password_reset/$', 'film20.account.views.password_reset', name="acct_passwd_reset"),
    url(r'^'+urls['RESET_PASSWORD']+'/$', 'film20.account.views.password_reset', name="acct_passwd_reset"),        
    
#    url(r'^logout/$', 'django.contrib.auth.views.logout', {"template_name": "account/logout.html"}, name="acct_logout"),
    url(r'^'+urls['LOGOUT']+'/$', 
#	'django.contrib.auth.views.logout', 
	'film20.account.views.logout',
#	{"template_name": "account/logout.html"}, 
	name="acct_logout"),
    
    url(r'^confirm_email/(\w+)/$', 'film20.emailconfirmation.views.confirm_email', name="acct_confirm_email"),
    url(r'^username_autocomplete/$', 'film20.account.views.username_autocomplete'),

    # ajax validation
    (r'^validate/$', 'ajax_validation.views.validate', {'form_class': SignupForm}, 'signup_form_validate'),
)
