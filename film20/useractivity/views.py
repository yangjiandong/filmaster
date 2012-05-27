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
from django.shortcuts import render_to_response, get_object_or_404
from film20.config.urls import templates, full_url
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.utils.translation import gettext as _

import json
import logging
logger = logging.getLogger(__name__)

from film20.useractivity.useractivity_helper import PlanetHelper
from film20.useractivity.useractivity_helper import PlanetFilmHelper
from film20.useractivity.useractivity_helper import PlanetPersonHelper
from film20.useractivity.useractivity_helper import PlanetTagHelper
from film20.useractivity.useractivity_helper import NUMBER_OF_ACTIVITIES
from film20.useractivity.watching_helper import WatchingHelper

from film20.utils.cache_helper import CACHE_FIVE_MINUTES
from film20.utils.utils import json_success, json_error

from film20.core.models import Film
from film20.core.models import Person

from film20.useractivity.models import UserActivity

from film20.useractivity.forms import ActivityForm, SuperForm
from film20.useractivity.forms import FakeActivityForm
# Create your views here.

from django.views.generic import detail, base, list
from film20.dashboard.forms import WallForm, FilmForm, PersonForm

from film20.core.views import PaginatorListView

from film20.config.urls import urls

class WallView(PaginatorListView, detail.SingleObjectMixin):
    post_form = True

    def get_template_names(self):
        if 'ajax' in self.request.GET:
            return ['wall/useractivity/ajax_show_activities.html', ]
        return super(WallView, self).get_template_names()

    def get_paginate_by(self, queryset):
        if self.request.POST and 'ajax' in self.request.GET:
            return 1
        return super(WallView, self).get_paginate_by(queryset)

    def create_wallpost(self, text, **extra):
        from film20.core.models import ShortReview
        wallpost = ShortReview.objects.create(
            kind=ShortReview.WALLPOST,
            user=self.request.user,
            object=self.object,
            review_text=text,
            type=ShortReview.TYPE_SHORT_REVIEW,
            **extra
        )
        return wallpost

    def post(self, *args, **kw):
        self.object = self.get_object()
        if self.request.user.is_authenticated():
            form = WallForm(self.request.POST)
            if form.is_valid():
                self.create_wallpost(form.cleaned_data['text'])
                if not 'ajax' in self.request.GET:
                    messages.add_message(self.request, messages.INFO, _('Wall post has been published'))

            elif self.request.is_ajax():
                result = {
                    'success': False,
                    'errors': dict([(k, [unicode(e) for e in v]) for k,v in form.errors.items()])
                }
                return HttpResponse( json.dumps( result ) )

        return self.get(*args, **kw)

    @property
    def is_filtered( self ):
        return self.request.GET.get( 'f', 'all' ) not in ( 'all', 'custom' )

    def get_activities(self):
        activities = UserActivity.objects
        if not self.is_filtered:
            activities = activities.filter( hidden=False )
        return activities.select_related("checkin__screening")
    
    def get_queryset(self):
        return self.get_activities().wall_filter(self.request)

    def get_context_data(self, **kwargs):
        context = super(WallView, self).get_context_data(**kwargs)

        path_url = self.request.path
        object_name = self.object._meta.object_name.lower() if self.object else ''
        
        context['activities'] = context['object_list']
        context['show_single'] = self.is_filtered or object_name in ( 'film', 'person' )
        context['custom_filter'] = self.request.user.is_authenticated() and self.request.user.get_profile().custom_dashboard_filter

        if self.object:
            context[object_name] = self.object
        if self.post_form:
            form = WallForm()
            if urls['FILM'] in path_url:
                form = FilmForm()
            if urls['PERSON'] in path_url:
                form = PersonForm()
            context['form'] = form
        return context
    
    def get_object(self):
        return None
    
    def get(self, *args, **kw):
        self.object = self.get_object()
        return super(WallView, self).get(*args, **kw)
        
    def get_context_object_name(self, obj):
        if obj is self.object:
            return detail.SingleObjectMixin.get_context_object_name(self, obj)
        return 'activities'

# Not used in Filmaster 2.0 but we'd like to have this feature back
def __return_to_object_view(request, form=None):
    if not form:
        # TODO: fix this handling some time... maybe
        if request.POST == None:
            return HttpResponseRedirect('/404/?subscribe_failed_post_none')
        else:
            return HttpResponseRedirect('/404/?subscribe_failed_post_ok')

    # TODO: maybe pass a parameter like ?subscribed or ?unsubscribed or ?error to indicate what happened
    return HttpResponseRedirect(form.object.get_child_absolute_url())

# Not used in Filmaster 2.0 but we'd like to have this feature back
def toggle_subscribe(request, ajax=False):
    """
        Subscribe to receive notifications for an object (post, short review, thread).
        If already subscribed, the action unsubscribes to stop receiving notices.
    """
    if request.POST:
        if not request.user.is_authenticated():
            if ajax:
                return json_error('LOGIN')
            else:
                return HttpResponseRedirect(full_url('LOGIN') + '?next=%s&reason=vote' % request.path)

        from film20.useractivity.forms import SubscribeForm
        form = SubscribeForm(request.POST)
        valid = form.is_valid()

        if not valid:
            if ajax:
                return json_error("Form not valid") # TODO: pass error?
            else:
                return __return_to_object_view(request, form)

        watching_helper = WatchingHelper()
        watching_helper.alter_watching_subscribed(request.user, form.object)

        if ajax:
            return json_success()
        else:
            return __return_to_object_view(request, form)
    # Not a POST - fail!
    else:
        if ajax:
            return json_error("Not a POST request!");
        else:
            return __return_to_object_view(request)

@login_required
def recent_answers(request):
    activities = None

    watching_helper = WatchingHelper()
    planet_helper = PlanetHelper()
    activities = watching_helper.recent_answers(request.user)

    if activities:
        activities = planet_helper.paginate_activities(request, activities)
    data = {
        'activities':activities,
    }

    return render_to_response(
            templates['RECENT_ANSWERS'],
            data,
            context_instance=RequestContext(request))

from django.shortcuts import render, get_object_or_404
def render_wallpost( request, id ):
    from film20.core.models import ShortReview
    
    wallpost = get_object_or_404( ShortReview, pk=id )
    return render( request, "profile/wall_post/body.html", { 'content': wallpost.review_text } )

def render_comment( request, id ):
    from film20.threadedcomments.models import ThreadedComment
    
    comment = get_object_or_404( ThreadedComment, pk=id )
    return render( request, "profile/wall_post/body.html", { 'content': comment.comment } )

@login_required
def subscribe(request):
    if request.method == "POST":
        from .forms import SubscribeForm
        form = SubscribeForm(request.POST, user=request.user)
        if form.is_valid():
            logger.info("HERE: %r", form.cleaned_data)
            form.save()
        else:
            print form.errors
    if 'HTTP_X_REQUESTED_WITH' in request.META:
        return HttpResponse('ok')
    next = request.REQUEST.get('next', request.META.get('HTTP_REFERER'))
    return HttpResponseRedirect(next or '/')

@login_required
def remove( request, id ):
    activity = get_object_or_404( UserActivity, pk=id )
    if activity.can_remove( request.user ):
        activity.remove( request.user )
        return json_success()
    return json_error( _( 'Cannot remove activity' ) )
