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
"""
Oldforms validators for tagging related fields - these are still
required for basic ``django.contrib.admin`` application field validation
until the ``newforms-admin`` branch lands in trunk.
"""
from django import forms
from django.utils.translation import ugettext as _

from tagging import settings
from tagging.utils import parse_tag_input

def is_tag_list(value):
    """
    Validates that ``value`` is a valid list of tags.
    """
    for tag_name in parse_tag_input(value):
        if len(tag_name) > settings.MAX_TAG_LENGTH:
            raise forms.ValidationError(
                _('Each tag may be no more than %s characters long.') % settings.MAX_TAG_LENGTH)
    return value

def is_tag(value):
    """
    Validates that ``value`` is a valid tag.
    """
    tag_names = parse_tag_input(value)
    if len(tag_names) > 1:
        raise ValidationError(_('Multiple tags were given.'))
    elif len(tag_names[0]) > settings.MAX_TAG_LENGTH:
        raise forms.ValidationError(
            _('A tag may be no more than %s characters long.') % settings.MAX_TAG_LENGTH)
    return value
