#-*- coding: utf-8 -*-
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

register = template.Library()

@register.simple_tag
def format_url(url):
    if url.startswith("http://") | url.startswith("https://"):
        return url
    else:
        return "http://" + url

@register.simple_tag
def unformat_url(url):
    if url.startswith("http://"): 
        return url.replace("http://", "")
    elif url.startswith("https://"):
        return url.replace("https://", "")
    else:
        return url
