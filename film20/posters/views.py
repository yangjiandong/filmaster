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

import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from film20.core.models import Film, Person
from film20.posters.models import ModeratedPhoto
from film20.posters.forms import PhotoForm, UploadedImageForm
from film20.upload.models import UserUploadedImage

@login_required
def add_photo( request, permalink, type, template = "posters/add-photo-form.html" ):
    """
    Photo add/replace
    """

    # get selected object
    if type == 'film': 
        obj = Film.objects.select_related().get( parent__permalink = permalink ) 
        url = reverse( 'add-poster', args=[obj.permalink] )

    elif type == 'person': 
        obj = Person.objects.select_related().get( parent__permalink=permalink, parent__status=1 )
        url = reverse( 'add-person-photo', args=[obj.permalink] )

    else:
        raise AttributeError 

    if obj is None:
        raise Http404
    
    if request.method == "POST":
        if request.is_ajax():
            form = UploadedImageForm( request.POST )
            result = {
                'success': False,
                'message': '',
                'can_accept': False
            }

            if form.is_valid(): 
                uploaded_image = get_object_or_404( UserUploadedImage, id=form.cleaned_data.get( "uploaded_image" ) )
                in_all_languages = form.cleaned_data.get( "in_all_languages" )
                is_main = form.cleaned_data.get( "is_main" )
                
                poster, message = save_poster( request, uploaded_image.image, obj, in_all_languages, is_main )
                
                result['success'] = True
                result['message'] = message
                result['can_accept'] = request.user.has_perm( 'posters.can_accept_posters' )

            else:
                result['message'] = _( "You must enter one of the options" )

            return HttpResponse( json.dumps( result ), mimetype="text/javascript" )

        else:
            form = PhotoForm( request.POST, request.FILES )
            if form.is_valid():
                image = form.cleaned_data.get( "photo" ) or form.cleaned_data.get( "url" )            
                in_all_languages = form.cleaned_data.get( "in_all_languages" )
                is_main = form.cleaned_data.get( "is_main" )

                poster, message = save_poster( request, image, obj, in_all_languages, is_main )

    else:
        form = PhotoForm()

    return render( request, template, {
        "url": url,
        "form": form,
        "type": type,
        "object": obj
    })

def save_poster( request, image, obj, in_all_languages, is_main ):
    poster = ModeratedPhoto(
        content_object = obj,
        user = request.user,
        image = image,
        in_all_languages = in_all_languages or False,
        is_main = is_main or False,
    )
    poster.save()

    # if user has perm to accept posters, do this now
    if request.user.has_perm( 'posters.can_accept_posters' ):
        poster.accept( request.user )
        obj = poster.content_object
        message = _( "Photo added!" )

    else: message = _( "Photo added! awaiting approval" )

    request.user.message_set.create( message=message )
    return poster, message

def image(request, permalink):
    from film20.utils.posters import get_image_path
    try:
        film = get_object_or_404(Film, permalink=permalink)
        width = request.GET.get('width')

        if not film.poster or not width in (None, '400', '600', '800'):
            raise Http404

        if width is None:
            size = ()
        else:
            size = (width, )

        path = get_image_path(film, *size)
        return HttpResponseRedirect(path)
    except Http404:
        return HttpResponse('not found', status=404)

