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
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE
from email.utils import formatdate
from time import strftime, mktime
import film20.utils.pretty as pretty

register = template.Library()

@register.simple_tag
def format_date(date):
    if LANGUAGE_CODE == 'pl':
        try:
            timedate = str(date)
            date, time = timedate.split(' ')
            hours, minutes, seconds = time.split(':')
            year, month, day = date.split('-')
            MONTHS = {
                "01" : 'stycznia',
                "02" : 'lutego',
                "03" : 'marca',
                "04" : 'kwietnia',
                "05" : 'maja',
                "06" : 'czerwca',
                "07" : 'lipca',
                    "08" : 'sierpnia',
                "09" : 'września',
               "10" : 'października',
               "11" : 'listopada',
               "12" : 'grudnia',
            }
            polish_month = ""
            if MONTHS.has_key(month):
                polish_month = MONTHS[month]
            return day+" "+polish_month+" "+year+', '+hours+':'+minutes
        except:
            return "BUG!!!"
    else:
        return date.strftime("%A %d. %B %Y, %H:%M")

@register.simple_tag
def rfc2822_date(date):
    date = mktime(date.timetuple())
    date = float(date)
    return formatdate(date)

@register.simple_tag
def human_readable_date(date):
    """
        Returns date in facebook-style
    """

    return pretty.date(date)

