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
from django.utils import simplejson
from django.utils.translation import gettext_lazy as _, gettext
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.contrib.auth.models import User
from django.contrib import messages

from film20.config.urls import *
from film20.core.models import Person, ShortReview, Object
from film20.dashboard.forms import WallForm
from film20.useractivity.models import UserActivity

from film20.useractivity.useractivity_helper import ajax_activity_pager, \
    ajax_select_template

import logging
logger = logging.getLogger(__name__)

from film20.useractivity.views import WallView
class ShowPersonView(WallView):
    template_name = 'person/person.html'

    def get_object(self):
        person = get_object_or_404(Person, permalink=self.kwargs['permalink'])
        person.parent = Object(id=person.parent_id)
        return person
    
    def get_activities(self):
        return UserActivity.objects.filter(person=self.object.pk)

def show_person(request, permalink):
    person = get_object_or_404(Person, permalink=permalink)

    form = WallForm(request.POST or None)
    if request.POST and request.user.is_authenticated() and form.is_valid():
        sr = ShortReview.objects.create(
                kind=ShortReview.WALLPOST,
                user=request.user,
                object=person,
                review_text=form.cleaned_data['text'],
                type=ShortReview.TYPE_SHORT_REVIEW,
        )
	messages.add_message(request, messages.INFO, gettext('Wall post has been published'))
	form = WallForm()
    
    activities = UserActivity.objects.wall_filter(request).filter(person=person)
    activities = ajax_activity_pager(request, activities)
    
    context = {
        'person':person,
        'form':form,
        'activities':activities,
    }
    return render(
        request,
        ajax_select_template(request, 'person/person.html'),
        context
    )

def show_person_old(request, permalink, ajax=None):

    # some defaults  
    the_person = None
    actor_already_rated = False
    actor_just_rated = False
    director_already_rated = False
    director_just_rated = False
    person_tag_form = None
    related_posts = None
    recent_comments = None
    films_played = None
    films_directed = None
    
    # helpers required 
    person_helper = PersonHelper()

    # TODO: move to decorator
    if (ajax!='json') & (ajax!=None):
        logger.error(_("Unsupported ajax type:"+ajax))
        # TODO: throw exception
        return None

    try:    
        # set to true if we are to edit the localized title
        is_edit_tags = person_helper.is_set(request.GET['is_edit_tags'])        
        logger.debug("is_edit_tags: " + unicode(is_edit_tags))
    except KeyError:
        is_edit_tags = False
    try:    
        # set to true if we are to edit the localized title
        is_edit_localized = person_helper.is_set(request.GET['is_edit_localized'])        
        logger.debug("is_edit_localized: " + unicode(is_edit_localized))
    except KeyError:
        is_edit_localized = False
        
        
     # Get film and connected values
    try:    
        the_person = person_helper.get_person(permalink)
        related_posts = person_helper.get_related_posts(permalink)
        recent_comments = person_helper.get_recent_comments(permalink)
        films_played = person_helper.get_films_played(the_person)
        films_directed = person_helper.get_films_directed(the_person)
    except Person.DoesNotExist:
        if ajax==None:
            return HttpResponseRedirect(full_url('SEARCH_PERSON')+permalink+'/')
        elif ajax=='json':
            # TODO: trans
            return json_error("Cannot find a person you are about to vote for.")
        
    # set context defaults    
    guess_rating = None            
    actor_rating_form = rating_helper.get_default_rating_form(the_person.parent.id, Rating.TYPE_ACTOR)      
    director_rating_form = rating_helper.get_default_rating_form(the_person.parent.id, Rating.TYPE_DIRECTOR)
    person_tag_form = person_helper.get_object_tag_form(the_person)
    person_localized_form = person_helper.get_person_localized_form(the_person)
            
    # Not authenticated, trying to vote -> redirect
    # TODO (WISH): perhaps somehow try to pass the parameters so that it automatically
    # tries to submit a vote when the user logs in successfully?
    if (not request.user.is_authenticated()) & (request.method == 'POST'):
        if ajax==None:
            return HttpResponseRedirect(full_url('LOGIN') + '?next=%s' % request.path) 
        elif ajax=='json':
            # TODO: trans
            return json_error("You have to be logged in to vote.")                                       
    
    # Populate context in case the user is authenticated
    if request.user.is_authenticated():                       
        logger.debug("User authenticated, getting personalized rating data.")
        
        actor_rating = rating_helper.get_rating_form(request.user.id, the_person.parent.id, Rating.TYPE_ACTOR)
        if actor_rating != None:
            actor_already_rated = True
        director_rating = rating_helper.get_rating_form(request.user.id, the_person.parent.id, Rating.TYPE_DIRECTOR)
        if director_rating != None:
            director_already_rated = True
            
        actor_rating_form = rating_helper.generate_rating_form(request.user.id, the_person.parent.id, Rating.TYPE_ACTOR, actor_rating)               
        director_rating_form = rating_helper.generate_rating_form(request.user.id, the_person.parent.id, Rating.TYPE_DIRECTOR, director_rating)
            
        # guess rating
        try:
            guess_rating = rating_helper.guess_score(user=request.user, object_id=the_person.parent.id)
        except Rating.DoesNotExist:
            guess_rating = None    
            
    if request.user.is_authenticated() & (request.method == 'POST'):
        form_id = request.POST['form_id']
        logger.debug("form_id="+unicode(form_id))
        if(form_id==LOCALIZED_PERSON_FORM_ID):
            logger.debug("Parsing the localized person form in person view")
            person_localized_form = person_helper.get_person_localized_form(the_person, request.POST)
            is_valid = person_helper.handle_edit_person_localized(the_person, person_localized_form)
            is_edit_localized = not is_valid
        elif(form_id==TAGGING_FORM_ID):
            logger.debug("Parsing the tagging form in film view.")
            person_tag_form = person_helper.get_object_tag_form(the_person, request.POST)       
            is_valid = person_helper.handle_edit_tag(the_person, person_tag_form)
            is_edit_tags = not(is_valid)
        else: 
            logger.debug("Parsing the rating form in person view.")                                
            processed_rating_form = rating_helper.handle_rating(RatingForm(request.POST), request.user)                                    
            
            if processed_rating_form.is_valid():
                form_type = int(processed_rating_form.cleaned_data['form_type'])
                if form_type == Rating.TYPE_ACTOR:
                    actor_just_rated = True         
                elif form_type == Rating.TYPE_DIRECTOR:
                    director_just_rated = True
            else:                
                try:
                    form_type =  int(request.POST['form_type'])
                except ValueError:
                    form_type = None
            
            if form_type == Rating.TYPE_ACTOR:
                actor_rating_form = processed_rating_form            
            elif form_type == Rating.TYPE_DIRECTOR:
                director_rating_form = processed_rating_form
            else:
                # if none, we should actually throw an exception perhaps and redirect page to error
                # since this means form hacking...
                logger.error("Unexpected form type. URL hacking?")
    
    if actor_just_rated:
        actor_already_rated = True
    if director_just_rated:
        director_already_rated = True
         
    actor_rating_form_ok = {'form':actor_rating_form,'type':Rating.TYPE_ACTOR,}
    director_rating_form_ok = {'form':director_rating_form,'type':Rating.TYPE_DIRECTOR,}
    
    if ajax=='json':
        return json_success()
    else:
        logger.debug("Non-ajax form, proceeding")
    
    context = {
        'the_person' : the_person,
        'related_posts' : related_posts,
        'recent_comments':recent_comments,
        'films_played': films_played,
        'films_directed': films_directed,
        'actor_rating_form' : actor_rating_form_ok,
        'director_rating_form' : director_rating_form_ok,
        'guess_rating' : guess_rating,
        'actor_just_rated' : actor_just_rated,
        'actor_already_rated' : actor_already_rated,
        'director_just_rated' : director_just_rated,
        'director_already_rated' : director_already_rated,
        
        'person_tag_form': person_tag_form,
        'TAGGING_FORM_ID': TAGGING_FORM_ID,
        'is_edit_tags' : is_edit_tags,
        
        'person_localized_form': person_localized_form,
        'is_edit_localized': is_edit_localized,
    }
    return render(
        request,
        templates['SHOW_PERSON'], 
        context
    )


from film20.core.models import ModeratedPersonLocalized

@login_required
def edit_person_localized_data( request, permalink, type ):
    allowed_types = [ 'name', 'biography' ]

    person = get_object_or_404( Person, permalink=permalink )
    def get_name():
        p = Person.objects.get( pk=person.pk )
        return [ 
            { 
                'name': 'name',
                'value': p.localized_name
            }, {
                'name': 'surname',
                'value': p.localized_surname
            }
        ]

    def get_biography():
        p = Person.objects.get( pk=person.pk )
        return p.biography

    result = { 'success': True }
    if type in allowed_types:
        if request.method == 'POST':
            v = request.POST['value']
            perm = request.user.has_perm( 'core.can_accept_localized_data' )

            if not perm:
                mp = ModeratedPersonLocalized.objects.create( person=person, user=request.user )

            if type == 'name':
                v_name = request.POST['v_name']
                v_surname = request.POST['v_surname']
                if perm:
                    person.localized_name = v_name
                    person.localized_surname = v_surname
                else:
                    mp.name = v_name
                    mp.surname = v_surname

                v = get_name()
        
            if type == 'biography':
                if perm:
                    person.biography = v
                else:
                    mp.biography = v

                v = get_biography()
        
            if not perm:
                result[ 'need_moderate' ] = True
                result[ 'message' ] = str( _( 'Element saved! awaiting approval' ) )
                mp.save()

            else:
                result['message'] = str( _( 'Element saved!' ) )

            
            result['value'] = v
        
        elif request.method == 'GET':
            if type == 'name':
                v = get_name()

            if type == 'biography':
                v = get_biography()

            result['value'] = v
        else:
            raise AttributeError
    else:
        raise AttributeError

    return HttpResponse( simplejson.dumps( result ), mimetype="application/json" )
