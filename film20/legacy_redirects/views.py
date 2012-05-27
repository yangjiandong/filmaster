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

from django.views.generic.simple import redirect_to
from django.http import Http404
from film20.core.urlresolvers import reverse
from film20.core.models import ShortReview
from django.conf import settings

def redirect_to_blog_post(request, username, permalink):

    kwargs = {
            'username': username,
            'permalink': permalink,
    }
    url = reverse('show_article', kwargs=kwargs)
    return redirect_to(request, url=url)

def redirect_to_short_review(request, username, permalink):

    try:
        shortreview = ShortReview.objects.select_related('object','user')\
                .get(kind=ShortReview.REVIEW, object__permalink=permalink,
                user__username=username)
    except ShortReview.DoesNotExist:
        raise Http404

    kwargs = {
            'username': username,
            'post_id': shortreview.id,
    }
    url = reverse('show_wall_post', kwargs=kwargs)
    return redirect_to(request, url=url)

def redirect_to_wff(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/wff/')
    raise Http404
def redirect_to_aff(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/aff/')
    raise Http404
def redirect_to_sputnik(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/sputnik/')
    raise Http404
def redirect_to_piec_smakow(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/piec-smakow/')
    raise Http404
def redirect_to_offcamera(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/offcamera/')
    raise Http404
def redirect_to_filmy_swiata(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/filmy-swiata/')
    raise Http404
def redirect_to_tofifest(request):
    if settings.LANGUAGE_CODE == 'pl':
        return redirect_to(request, '/festiwal/tofifest/')
    raise Http404
def redirect_to_raindance(request):
    if settings.LANGUAGE_CODE == 'en':
        return redirect_to(request, '/festival/raindance/')
    raise Http404
def redirect_to_lff(request):
    if settings.LANGUAGE_CODE == 'en':
        return redirect_to(request, '/festival/lff/')
    raise Http404

