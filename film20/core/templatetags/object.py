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
from django.utils.translation import gettext_lazy as _, gettext
from django import template

from film20.config.urls import *

from django.conf import settings

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.inclusion_tag('widgets/tags.html', takes_context=True)
def object_tags(context, object, edit=False):
    tags = filter(bool, (t.strip() for t in object.get_tags().split(',')))
    return {
        'object':object,
        'perms':edit and context.get('perms') or {},
        'tags':tags,
    }

@register.inclusion_tag('widgets/score.html', takes_context=True)
def score(context, score):
    return {
        'score':score,
    }
