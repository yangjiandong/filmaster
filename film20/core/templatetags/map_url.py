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
from django.core import urlresolvers

from film20.config import *
from film20.core.models import Film

from django.contrib.auth.models import User
from film20.core.models import Object
from django.utils.translation import ugettext as _
from film20.externallink.models import ExternalLink

from django.conf import settings
MAX_USERNAME_LENGTH_DISPLAY = getattr(settings, "MAX_USERNAME_LENGTH_DISPLAY", 12)
SUBDOMAIN_AUTHORS = getattr(settings, "SUBDOMAIN_AUTHORS", False)
DOMAIN = getattr(settings, "DOMAIN", '')
FULL_DOMAIN = getattr(settings, "FULL_DOMAIN", '')

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.simple_tag
def map_domain():
    return FULL_DOMAIN

@register.simple_tag
def contact_admin():
    return "<a href=\"mailto:filmaster@filmaster.pl\">filmaster@filmaster.pl</a>"

@register.simple_tag
def map_url(url_name):
    the_url = FULL_DOMAIN
    if urls.urls[url_name]!="":
        the_url += "/" + urls.urls[url_name]
    return the_url

from django.core.urlresolvers import reverse
@register.simple_tag(takes_context=True)
def abs_url(context, url_name):
    domain = settings.DOMAIN
    if context['request'].subdomain:
        subdomain = context['request'].subdomain+'.'
    else:
        subdomain = ''
    url = reverse(url_name)
    abs_url = 'http://' + subdomain + domain + url
    return abs_url

@register.simple_tag
def map_url_part(url_name):
    return "/" + urls.urls[url_name]

@register.simple_tag
def url_object(the_object):
    if the_object.type == Object.TYPE_FILM:
        return url_film(the_object)
    elif the_object.type == Object.TYPE_PERSON:
        return url_person(the_object)
    # TODO: add note

@register.simple_tag
def url_film(the_film, extra=None):

    # This is done in case not a Film instance is passed as an argument to this method
    # It should not be happening but it did when changing the Apache mode to prefork
    # due to some issues with the cookies (or some other reason that was hard to spot)
    if not isinstance(the_film, Film):
        logger.error("Not an instance of class Film: " + str(the_film))
        return str(the_film)

    the_url = ""
    
    the_url += "<a href=\""+FULL_DOMAIN+"/"+ urls.urls['FILM'] +"/" + the_film.permalink +"/\">"
     
    try:
        title = the_film.get_title()
    except:
        logging.warn("Title could not be retrieved using film.get_title(). Returning from title field instead: " + unicode(the_film.title))
        title = the_film.title
    if extra=="short":
        the_url += title[:28]
        if len(title)>28:
            the_url += "..."
    else:
        the_url += title

    if extra==None:
        if the_film.release_year:
            the_url += " [" + unicode(the_film.release_year) + "]"
    the_url += "</a>"
    
    return the_url

@register.simple_tag
def permalink_film(the_film):
    if the_film:
        the_permalink = FULL_DOMAIN+"/"+ urls.urls['FILM'] +"/" + the_film.permalink +"/"
        return the_permalink

@register.simple_tag
def url_person(the_person):
    the_url = ""
    
    the_url += "<a href=\""+FULL_DOMAIN+"/"+ urls.urls['PERSON'] +"/" + the_person.permalink +"/\">"
    the_url += the_person.format()
    
    the_url += "</a>"
    
    return the_url

@register.simple_tag
def url_username_link(username, rest=None):
    if SUBDOMAIN_AUTHORS:
        the_url = "http://"
        the_url += unicode(username) + "." + DOMAIN
    else:
        the_url = "/" + urls.urls['SHOW_PROFILE'] + "/" + unicode(username)

    if rest:
        the_url += "/" + urls.urls[rest]
    return the_url

@register.simple_tag
def url_user_link(user, rest=None):
    return url_username_link(user.username, rest)

# TODO - move to the same tagtemplates where poster is
import os
@register.simple_tag
def poster_default():
    return FULL_DOMAIN + urls.urls['DEFAULT_POSTER']

@register.simple_tag
def link_title(link):
    return link.get_title()

@register.simple_tag
def link_link(the_link):
    return the_link.get_absolute_url()
    
@register.simple_tag
def url_link(link):
    the_url = ""
    the_url += "<a href=\""+link.get_absolute_url() +"\" rel=\"nofollow\">"+link.get_title()+"</a>"
    return the_url

@register.simple_tag
def facebook_url():
    """Returns url to our facebook fan page."""

    return "<a href= " + getattr(settings, 'FACEBOOK_URL') + ">"

@register.simple_tag
def twitter_url():
    """Returns url to our Twitter page."""

    return "<a href= " + getattr(settings, 'TWITTER_URL') + ">"

@register.simple_tag
def wff_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'wff' in tags:
            return "<a href=\"http://filmaster.pl/wff\"><img src=\"/static/img/pl/wff.png\" /></a> "
        else:
            return ""
    else:
        return ""
    
@register.simple_tag
def piec_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'pięć smaków' in tags:
            return "<a href=\"http://filmaster.pl/piec-smakow\"><img src=\"/static/img/pl/5.png\" /></a> "
        else:
            return ""
    else:
        return ""
    
@register.simple_tag
def lff_pl_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'bfi53' in tags:
            return "<a href=\"http://filmaster.pl/lff\"><img src=\"/static/img/en/lff.png\" /></a> "
        else:
            return ""
    else:
        return ""

@register.simple_tag
def lff_en_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'bfi53' in tags:
            return "<a href=\"http://filmaster.com/lff\"><img src=\"/static/img/en/lff.png\" /></a> "
        else:
            return ""
    else:
        return "" 
    
@register.simple_tag
def sputnik_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'sputnik' in tags:
            return "<a href=\"http://filmaster.pl/sputnik\"><img src=\"/static/img/pl/sputnik.png\" /></a> "
        else:
            return ""
    else:
        return ""

@register.simple_tag
def alekino5_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'alekino5' in tags:
            return "<a href=\"http://filmaster.pl/alekino5\"><img src=\"/static/img/pl/alekino5.png\" /></a> "
        else:
            return ""
    else:
        return ""       

@register.simple_tag
def off3_tag(the_film):
    if the_film:
        tags = the_film.get_tags()
        if 'off3' in tags:
            return "<a href=\"http://filmaster.pl/tag/off3\"><img src=\"/static/img/pl/off_3s.png\" /></a> "
        else:
            return ""
    else:
        return ""

@register.simple_tag
def private_message_to_user(user):

    url = FULL_DOMAIN + "/" + urls.urls['PW_COMPOSE'] + "/" + user.username
    return url

@register.simple_tag
def admin_change_url( module, id, next=None ):
    url = FULL_DOMAIN + urlresolvers.reverse( 'admin:%s_change' % module, args=( id, ) )
    if next:
        url += "?next=%s" % next
    return url
