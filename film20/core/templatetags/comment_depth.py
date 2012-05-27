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
from django import template
from film20.config import *
from film20.threadedcomments.models import ThreadedComment

register = template.Library()

@register.simple_tag
def comment_depth(commentDepth):
    commentDepth = int(commentDepth)
    if commentDepth == 0:
        return 0
    elif commentDepth == 1:
        return 1
    elif commentDepth == 2:
        return 2 
    else:
        return 2
    
@register.simple_tag
def number_of_comments(object):
    if object is None:
        return 0
    if object.number_of_comments:
        return object.number_of_comments
    else:
        return 0

@register.simple_tag
def number_of_comments_thread(thread):
    #count = ThreadedComment.objects.filter(object_id=thread.id).count()
    if thread.number_of_comments:
        return thread.number_of_comments - 1
    else:
        return 0

@register.simple_tag
def thread_parent(thread):
    thread_parent = ""
    if thread.forum.person_forum:
        thread_parent = thread.forum.person_forum.name + " " + thread.forum.person_forum.surname
    elif thread.forum.film_forum:
        thread_parent = thread.forum.film_forum.title
    else:
        thread_parent = thread.forum.title        
    return thread_parent
