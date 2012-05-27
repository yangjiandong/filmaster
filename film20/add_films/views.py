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

from django import http
from django.db.models import Q
from django.conf import settings
from django.utils.html import escape
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect

from film20.config.urls import templates
from film20.utils.slughifi import slughifi
from film20.add_films.utils import clear_actors_cache, clear_directors_cache
from film20.core.models import Country, Film, Person, Character
from film20.add_films.forms import AddFilmForm, PersonForm, FilmCastForm
from film20.add_films.models import AddedFilm, AddedCharacter

@login_required
def add_film( request ):
    if request.method == 'POST':
        form = AddFilmForm( request.POST, request.FILES )
        if form.is_valid():
            added_film = form.save( commit=False )
            added_film.user = request.user

            added_film.save()
            
            # manualy add production countries
            countries = form.cleaned_data['production_country']
            for country in countries:
                country, created = Country.objects.get_or_create( country=country )
                added_film.production_country.add( country )

            # ... and actors
            actors = form.cleaned_data['actors']
            importance = 1
            for actor, role in actors:
                a = AddedCharacter( added_film = added_film, person = actor, 
                                   character = role, importance = importance )
                a.save()
                importance += 1

            # ... and directors
            directors = form.cleaned_data['directors']
            for director in directors:
                added_film.directors.add( director )

            added_film.save()

            # if user has perm to accept film, do this now
            if request.user.has_perm( 'add_films.can_accept_added_films' ):
                added_film.accept( request.user )
                message = _( "Film added!" )

            else: message = _( "Film added! awaiting approval" )

            request.user.message_set.create( message=message )
            return redirect( "edit-added-film", id=added_film.id )

    else:
        form = AddFilmForm()

    return render_to_response( templates["ADD_FILM_MANUAL"], {
        "form": form,
    }, context_instance=RequestContext( request ) )


@login_required
def edit_film( request, id ):
    
    added_film = get_object_or_404( AddedFilm, id = id )
    
    moderated = added_film.moderation_status != AddedFilm.STATUS_UNKNOWN
    accepted = added_film.moderation_status == AddedFilm.STATUS_ACCEPTED
    
    form = None

    if request.user.has_perm( 'add_films.can_accept_added_films' ):
        if not moderated:
            if request.method == "POST":

                if 'reject' in request.POST: 
                    added_film.reject( request.user )
                    
                    return redirect( "moderation" )

                elif 'accept' in request.POST or \
                        'save' in request.POST:

                    form = AddFilmForm( request.POST, request.FILES, instance=added_film )
                    if form.is_valid():
                        added_film = form.save( commit=False )
                        
                        # clear and manualy add production countries
                        added_film.production_country.clear()

                        countries = form.cleaned_data['production_country']
                        for country in countries:
                            country, created = Country.objects.get_or_create( country=country )
                            added_film.production_country.add( country )
                    
                        # ... actors to
                        added_film.actors.clear()
                        
                        actors = form.cleaned_data['actors']
                        importance = 1
                        for actor, role in actors:
                            a = AddedCharacter( added_film = added_film, person = actor, 
                                               character = role, importance=importance )
                            a.save()
                            importance += 1

                        # ... and directors
                        added_film.directors.clear()
                        
                        directors = form.cleaned_data['directors']
                        for director in directors:
                            added_film.directors.add( director )

                        # at last accept this movie
                        added_film.save()
                        
                        if 'accept' in request.POST:
                            added_film.accept( request.user )

                        return redirect( "moderation" )

            else:
                form = AddFilmForm( instance=added_film )

    return render_to_response( "movies/add-movie-detail.html", {
        "added_film": added_film,
        "form": form,
        "moderated": moderated,
        "accepted": accepted
    }, context_instance=RequestContext( request ) )


@login_required
def edit_cast( request, permalink ):
    film = get_object_or_404( Film, parent__permalink = permalink )
    form = None
    if request.user.has_perm( 'add_films.can_edit_film_cast' ):
        if request.method == "POST":
            form = FilmCastForm( request.POST, instance=film )
            if form.is_valid():
                
                actors = form.cleaned_data['actors']
                
                # TODO: get from settings !?
                all_languages = ['en', 'pl']
                tmp_actors = {}
                for lang in all_languages:
                    tmp_actors[lang] = []
                
                importance = 0
                for actor, role in actors:
                    importance += 1
                    
                    for lang in all_languages:
                        character = role
                        if lang != settings.LANGUAGE_CODE:
                            try:
                                cache_ch = Character.objects.get( film = film, person = actor,
                                                           LANG = lang )
                                character = cache_ch.character
                            except Exception: 
                                pass # ignore DoesNotExist or Multiple Result
                        
                        ch = Character(
                            film = film, person = actor, character = character, 
                            importance = importance, LANG = lang )

                        tmp_actors[lang].append( ch )
                
                # clear actors
                film.actors.clear()
                
                # add new actors
                for lang in all_languages:
                    for actor in tmp_actors[lang]:
                        actor.save()
 
                # directors
                film.directors.clear()               
                directors = form.cleaned_data['directors']
                for director in directors:
                    film.directors.add( director )

                # ... and clear cache
                clear_actors_cache( film )
                clear_directors_cache( film )

                return redirect( film )

        else:
            form = FilmCastForm( instance=film )
    
    return render_to_response( "movies/movie/edit-cast.html", {
        "film": film,
        "form": form,
    }, context_instance=RequestContext( request ) )

@login_required
def add_person( request ):
    if request.method == "POST":
        form = PersonForm( request.POST )
        if form.is_valid():
            person = form.save( commit=False )
            person.permalink = slughifi( "%s %s" % ( person.name, person.surname ) )
            
            try:
                # if person with same permalink already exist
                #   we should return this person silent.
                person = Person.objects.get( permalink = person.permalink )
            except Person.DoesNotExist:
                person.type = Person.TYPE_PERSON
                person.save()

            if person:
                return http.HttpResponse( 
                    '<script type="text/javascript">opener.dismissAddAnotherPopup( window, "%s", "%s" );</script>' % ( 
                        person.pk, escape( person ) 
                    ))
    else:
        form = PersonForm()

    return render_to_response( "person/add-person-popup.html", {
        'form': form
    })

def ajax_country_list( request ):
    out = ""
    query = request.GET.get('q', None)
    if query:
        instances = Country.objects.filter( Q( country__istartswith=query ) )[:10]
        for item in instances:
            out += "%s\n" % ( item.country )

    return http.HttpResponse( out, mimetype='text/plain' )

from film20.search.views import PersonAutocompleteView
class PersonWithIdAutocompleteView( PersonAutocompleteView ):
    def mapping( self, person, type ):
        value = ( "%s %s" % ( person.name, person.surname ) ).replace( '|', '&verticalline;' )
        return "%d|%s" % ( person.id, value )

ajax_person_list = PersonWithIdAutocompleteView.as_view()
