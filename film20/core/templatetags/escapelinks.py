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
import re
from django import template
from django.template.defaultfilters import stringfilter

import film20.settings as settings
MAX_URL_LENGTH = getattr(settings, "MAX_URL_LENGTH", None)

register = template.Library()

@register.filter
@stringfilter
def escapelinks(value):
    "Removes all links in value string"
    return re.sub(r'<a[^>]*>([^<]*)</a>', r'\1', value)

#TODO the escape urls filter should be way smarter and should escape any type of protocol
@register.filter
@stringfilter
def escapeurls(value):
    "Removes all urls in value string"
    value = value + " " # stupid hack to make sure there is always a white space after a link
    return re.sub(r'http[s]*:\/\/\S*\s', r'[link]', value)

