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
from django.conf.urls.defaults import patterns, url
from models import FreeThreadedComment
import views

free = {'model' : FreeThreadedComment}

urlpatterns = patterns('',
    ### Comments ###
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.comment, name="tc_comment"),
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/$', views.comment, name="tc_comment_parent"),
    url(r'^comment/(?P<object_id>\d+)/delete/$', views.comment_delete, name="tc_comment_delete"),
    url(r'^comment/(?P<edit_id>\d+)/edit/$', views.comment, name="tc_comment_edit"),
    
    ### Comments (AJAX) ###
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<ajax>json|xml)/$', views.comment, name="tc_comment_ajax"),
    url(r'^comment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/(?P<ajax>json|xml)/$', views.comment, name="tc_comment_parent_ajax"),
    url(r'^comment/(?P<edit_id>\d+)/edit/(?P<ajax>json|xml)/$', views.comment, name="tc_comment_edit_ajax"),

    ### Free Comments ###
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/$', views.free_comment, name="tc_free_comment"),
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/$', views.free_comment, name="tc_free_comment_parent"),
    url(r'^freecomment/(?P<object_id>\d+)/delete/$', views.comment_delete, free, name="tc_free_comment_delete"),
    url(r'^freecomment/(?P<edit_id>\d+)/edit/$', views.free_comment, name="tc_free_comment_edit"),

    ### Free Comments (AJAX) ###
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<ajax>json|xml)/$', views.free_comment, name="tc_free_comment_ajax"),
    url(r'^freecomment/(?P<content_type>\d+)/(?P<object_id>\d+)/(?P<parent_id>\d+)/(?P<ajax>json|xml)/$', views.free_comment, name="tc_free_comment_parent_ajax"),
    url(r'^freecomment/(?P<edit_id>\d+)/edit/(?P<ajax>json|xml)/$', views.free_comment, name="tc_free_comment_edit_ajax"),
)
