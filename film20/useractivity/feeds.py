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
from django.template import loader
from django.template import Context
from django.http import HttpResponse
from django.http import Http404
from film20.config.urls import templates
from django.views.decorators.cache import cache_page

from django.contrib.auth.models import User
from film20.core.models import Film
from film20.core.models import Person
from film20.useractivity.useractivity_helper import PlanetHelper
from film20.useractivity.useractivity_helper import PlanetFilmHelper
from film20.useractivity.useractivity_helper import PlanetPersonHelper
from film20.useractivity.useractivity_helper import PlanetTagHelper
from film20.useractivity.watching_helper import WatchingHelper

ITEMS_PER_FEED = 20

@cache_page(60 * 5)
def planeta_rss(request, kind=None): 
    activities = None
    
    planet_helper = PlanetHelper(ITEMS_PER_FEED)
    
    if kind == "all":
        activities = planet_helper.planet_all()
    elif kind == "followers":
        followers_list = planet_helper.get_followers_list(request.user)
        activities = planet_helper.planet_followers(followers_list)
    elif kind == "similar_users":
        similar_users_list = planet_helper.get_similar_users_list(request)
        activities = planet_helper.planet_similar_users(similar_users_list)
    elif kind == "short_reviews":
        activities = planet_helper.planet_short_reviews()
    elif kind == "notes":
        activities = planet_helper.planet_notes()
    elif kind == "comments":
        activities = planet_helper.planet_comments()                    
    elif kind == "most_interesting":
        activities = planet_helper.planet_most_interesting() 
    elif kind == "links":
        activities = planet_helper.planet_links()                        
        
    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['PLANET_RSS'])
    c = Context({'activities': activities,'kind': kind})
    response.write(t.render(c))
    return response
    
@cache_page(60 * 5)
def film_planet_rss(request,  permalink, kind=None):
    activities = None
    the_film = None
    try:
        the_film = Film.objects.get(permalink=permalink)
    except Film.DoesNotExist:
        raise Http404
    
    planet_helper = PlanetFilmHelper(the_film, ITEMS_PER_FEED)
    if kind == "all":
        activities = planet_helper.planet_film_all()
    elif kind == "friends":
        friends_list = planet_helper.get_friends_list(request)
        activities = planet_helper.planet_film_friends(friends_list)
    elif kind == "similar_users":
        similar_users_list = planet_helper.get_similar_users_list(request)
        activities = planet_helper.planet_film_similar_users(similar_users_list)
    elif kind == "short_reviews":
        activities = planet_helper.planet_film_short_reviews()
    elif kind == "notes":
        activities = planet_helper.planet_film_notes()
    elif kind == "comments":
        activities = planet_helper.planet_film_comments() 
        
    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['PLANET_RSS'])
    c = Context({'activities': activities,'the_film':the_film,'kind':kind})
    response.write(t.render(c))
    return response    

@cache_page(60 * 5)
def person_planet_rss(request,  permalink, kind=None):
    activities = None
    person = None
    try:
        person = Person.objects.select_related().get(permalink=permalink)
    except Person.DoesNotExist:
        raise Http404
    planet_helper = PlanetPersonHelper(person, ITEMS_PER_FEED)  
    if kind == "all":
        activities = planet_helper.planet_person_all()
    elif kind == "friends":
        friends_list = planet_helper.get_friends_list(request)
        activities = planet_helper.planet_person_friends(friends_list)
    elif kind == "similar_users":
        similar_users_list = planet_helper.get_similar_users_list(request)
        activities = planet_helper.planet_person_similar_users(similar_users_list)
    elif kind == "short_reviews":
        activities = planet_helper.planet_person_short_reviews()
    elif kind == "notes":
        activities = planet_helper.planet_person_notes()
    elif kind == "comments":
        activities = planet_helper.planet_person_comments()     

    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['PLANET_RSS'])
    c = Context({'activities': activities,'person':person,'kind':kind})
    response.write(t.render(c))
    return response    

@cache_page(60 * 5)
def tag_planet_rss(request, tag=None, kind=None): 
    activities = None
    
    planet_helper = PlanetTagHelper(ITEMS_PER_FEED, tag=tag)
    
    if kind == "all":
        activities = planet_helper.planet_tag_all()
    elif kind == "friends":
        friends_list = planet_helper.get_friends_list(request)
        activities = planet_helper.planet_tag_friends(friends_list)
    elif kind == "similar_users":
        similar_users = planet_helper.get_similar_users_list(request)
        activities = planet_helper.planet_tag_similar_users(similar_users)
    elif kind == "short_reviews":
        activities = planet_helper.planet_tag_reviews()
    elif kind == "notes":
        activities = planet_helper.planet_tag_notes()
    elif kind == "comments":
        activities = planet_helper.planet_tag_comments()                              
        
    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['PLANET_RSS'])
    c = Context({'activities': activities,'kind': kind})
    response.write(t.render(c))
    return response

@cache_page(60 * 5)
def recent_answers_rss(request, username=None):
    
    user = None
    if username==None:
        raise Http404
    else:
        try:
            # TODO: case
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404
            
    activities = None
    watching_helper = WatchingHelper(ITEMS_PER_FEED)
    activities = watching_helper.recent_answers(user)
        
    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['PLANET_RSS'])
    c = Context({'activities': activities,'kind': 'recent_answers', 'username':username,})
    response.write(t.render(c))
    return response
