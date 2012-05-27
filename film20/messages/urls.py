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
from django.views.generic.simple import redirect_to

from film20.config.urls import urls
from django.core.urlresolvers import reverse

urlpatterns = patterns('film20.messages.views',
    # TODO - how to use reverse here ?
    url(r'^$', redirect_to, {'url': '/%(PW)s/%(PW_INBOX)s/' % urls}, name="messages"),
    url(r'^%(PW_INBOX)s/$' % urls, 'recent_conversations', name='messages_inbox'),
    url(r'^%(PW_OUTBOX)s/$' % urls, 'sent_messages', name='messages_outbox'),
    url(r'^%(PW_COMPOSE)s/$' % urls, 'compose', name='messages_compose'),
    url(r'^%(PW_COMPOSE)s/(?P<recipient>[\+\w]+)/$' % urls, 'compose', name='messages_compose_to'),
    url(r'^%(PW_REPLY)s/(?P<message_id>[\d]+)/$' % urls, 'reply', name='messages_reply'),
    url(r'^%(PW_VIEW)s/(?P<message_id>[\d]+)/$' % urls, 'view', name='messages_detail'),
    url(r'^%(PW_CONV_VIEW)s/(?P<id>[\d]+)/$' % urls, 'view_conversation', name='messages_view_conversation'),
    url(r'^%(PW_DELETE)s/(?P<message_id>[\d]+)/$' % urls, 'delete', name='messages_delete'),
    url(r'^%(PW_CONV_DELETE)s/(?P<id>\d+)/$' % urls, 'delete_conversation', name='messages_delete_conversation'),
)
