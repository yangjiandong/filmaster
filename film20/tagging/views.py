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
Tagging related views.
"""
import json

from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.shortcuts import render, get_object_or_404
from django.views.generic.list_detail import object_list
from django.contrib.auth.decorators import login_required

from film20.tagging.models import Tag, TagAlias, TaggedItem, TagTranslation
from film20.tagging.utils import get_tag, get_queryset_and_model

@never_cache
def get_tag_aliases( request, tag ):
    tag = get_object_or_404( Tag, name=tag )
    aliases = []
    for alias in TagAlias.objects.filter( tag=tag ):
        aliases.append( alias.name )
    return HttpResponse( json.dumps( { 'result': ', '.join( aliases ) } ) )

@never_cache
def get_tag_translation( request, tag ):
    return HttpResponse( json.dumps( { 'tag': tag, 'result': TagTranslation.translate( tag ) } ) )

@never_cache
@login_required
def objects_tagget_with( request, tag ):
    tag = get_object_or_404( Tag, name=tag )
    items = TaggedItem.objects.filter( tag=tag )
    
    ctx = {
        'tag': tag,
        'items': items
    }

    return render( request, "moderation/rename_tag/taggeditems.html", ctx )

def tagged_object_list(request, queryset_or_model=None, tag=None,
        related_tags=False, related_tag_counts=True, **kwargs):
    """
    A thin wrapper around
    ``django.views.generic.list_detail.object_list`` which creates a
    ``QuerySet`` containing instances of the given queryset or model
    tagged with the given tag.

    In addition to the context variables set up by ``object_list``, a
    ``tag`` context variable will contain the ``Tag`` instance for the
    tag.

    If ``related_tags`` is ``True``, a ``related_tags`` context variable
    will contain tags related to the given tag for the given model.
    Additionally, if ``related_tag_counts`` is ``True``, each related
    tag will have a ``count`` attribute indicating the number of items
    which have it in addition to the given tag.
    """
    if queryset_or_model is None:
        try:
            queryset_or_model = kwargs.pop('queryset_or_model')
        except KeyError:
            raise AttributeError(_('tagged_object_list must be called with a queryset or a model.'))

    if tag is None:
        try:
            tag = kwargs.pop('tag')
        except KeyError:
            raise AttributeError(_('tagged_object_list must be called with a tag.'))

    tag_instance = get_tag(tag)
    if tag_instance is None:
        raise Http404(_('No Tag found matching "%s".') % tag)
    queryset = TaggedItem.objects.get_by_model(queryset_or_model, tag_instance)
    if not kwargs.has_key('extra_context'):
        kwargs['extra_context'] = {}
    kwargs['extra_context']['tag'] = tag_instance
    if related_tags:
        kwargs['extra_context']['related_tags'] = \
            Tag.objects.related_for_model(tag_instance, queryset_or_model,
                                          counts=related_tag_counts)
    return object_list(request, queryset, **kwargs)
