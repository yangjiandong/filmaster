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
from django.db.models import Q
from django.db import transaction

from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Rating
from film20.core.models import RatingComparator
from film20.core.models import FilmComparator
from film20.core.models import FilmRanking
from film20.core.models import Recommendation
from film20.core.models import FilmLocalized
from film20.core.models import ObjectLocalized
from film20.tagging.models import Tag, TaggedItem
from film20.utils import cache
from film20.recommendations.synopsis_helper import *

from django.contrib.auth.models import User
from django.db import connection, transaction, models
from django.conf import settings

from decimal import *
from datetime import datetime
from datetime import date
from datetime import timedelta
from math import pow, sqrt

from film20.core.film_helper import FilmHelper
from film20.recommendations.recom_helper import RecomHelper
from film20.core import rating_helper


LANGUAGE_CODE = settings.LANGUAGE_CODE
DEFAULT_FETCHER = settings.DEFAULT_FETCHER
DATABASE_NAME = settings.DATABASE_NAME
DATABASE_USER = settings.DATABASE_USER

import os
import subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

import logging
logger = logging.getLogger(__name__)

DEBUG = True
DEBUG_DETAILED = False
#DEBUG_DETAILED = True

DEBUG_USING_LOGGING = True

#DEBUG_DETAILED = True
#DEBUG = False
# TODO: use django-logging?

MIN_FILMS_COMPARED = 10
MIN_RATINGS = 10

def do_normalize_votes():
    """
        Normalizes the votes of all users 
    """
    debug("Normalizing votes for users...")
    users = User.objects.all()
    users_count = users.count()
    # for all users
    for curuser in users:
        normalize_votes_for_user(curuser)
    debug("Normalized votes for all users.")
    return

def normalize_votes_for_user(curuser):
    """
        Normalizes the votes of curuser 
    """
    ddebug(unicode(curuser))
        
    accum_films = 0
    accum_votes = 0
   
    # get all ratings for user
    curuser_ratings = Rating.objects.filter(
        user__username=curuser.username,
        rating__isnull=False
    )
    for curuser_rating in curuser_ratings:                            
        if curuser_rating.rating:
                accum_films = accum_films+1
                accum_votes = accum_votes + curuser_rating.rating
                            
    ddebug('films scanned: ' + unicode(accum_films))
    ddebug('accum. votes: ' + unicode(accum_votes))
        
    if accum_films != 0:
        average_rating = float(accum_votes)/float(accum_films)        
        for curuser_rating in curuser_ratings:
            old_rating = curuser_rating.rating
            new_rating = get_normalized_vote(rating=curuser_rating.rating, average=average_rating)          
            curuser_rating.normalized = unicode(new_rating)
            curuser_rating.save() 
            ddebug("Normalized rating for " + curuser_rating.parent.permalink + ". Old: " + unicode(old_rating) + ", new: " + unicode(new_rating) + ".")
        ddebug("Normalized " + unicode(accum_films) + " votes for " + unicode(curuser))            
    else:
        ddebug("No votes to normalize for " + unicode(curuser))
        
    return

def get_normalized_vote(rating, average):
    """
        Normalizes a vote using "algorithm" N1 described in SAD 
    """
    diff = average-5
    new_rating = rating-diff
    return new_rating

def do_create_comparators(only_new_users=False):
    """
        For each ``User``, creates ``RatingComparator`` objects that link the user
        with any other user in the system. For each such relationship, the value is 
        computed to represent the user's common taste indicator basing on the algorithm
        described in Software Architecture Document 
    """
    debug("Creating comparators for users...")
    
    today = datetime.today()
    since = today - timedelta(days=1)
    if only_new_users: 
#        users = User.objects.filter(date_joined__gte = since)
        users = User.objects.all()
        users = users.extra(
            where = ["id IN (select distinct user_id from core_rating where rating is not null and last_rated>'%s')" % since]
        )
    else:
        users = User.objects.all()
    users_count = users.count()
    
    # for all users
    all_users = User.objects.all()
    
    for i, curuser in enumerate(users):
        debug("%d/%d %s" % (i+1, users_count, curuser))
        create_comparators_for_user(curuser, all_users)
    debug("Created comparators for " + unicode(users_count)  + " users.")
    return


def create_comparators_for_user(curuser, all_users=None):
    """
        Creates ``RatingComparator`` objects that link the user ('curuser')
        with any other user in the system. For each such relationship, the value is 
        computed to represent the user's common taste indicator basing on the algorithm
        described in Software Architecture Document 
    """
    ddebug("Creating comparators for " + unicode(curuser))
    
    if all_users == None:
        all_users = User.objects.all()
    
    q_users_with_comparator = ( 
        Q(compared_users__main_user__id = curuser.id) 
    )
    
    # GET ALL USERS WITH COMPARATORS
    users_with_comparators = User.objects.filter(q_users_with_comparator).distinct()
    users_with_comparators_cnt = users_with_comparators.count()
    
    comparators_created = 0
        
    ddebug("Computing taste for users with comparators for " + unicode(curuser.username) + " = " + unicode(users_with_comparators_cnt))
    for compared_user in users_with_comparators:
        ddebug("Compared user (with comparator) = " + unicode(compared_user))
        if compared_user.username != curuser.username:
            create_comparator_for_two_users(curuser, compared_user, new_user=False)
            comparators_created = comparators_created+1

    # GET ALL USERS WITHOUT COMPARATORS (the rest of users)
    ddebug("Computing taste for users without comparators for " + unicode(curuser.username))
    for compared_user in all_users:
        if not compared_user in users_with_comparators:
            ddebug("Compared user (w/o comparator) = " + unicode(compared_user))
            if compared_user.username != curuser.username:
                create_comparator_for_two_users(curuser, compared_user, new_user=True)
                comparators_created = comparators_created+1
    return comparators_created

def create_comparator_for_two_users(curuser, compared_user, new_user=False):
    
    # data for creating a RatingComparator object
    oryg_films_compared = 0
    films_compared = 0
    sum_difference = 0
    comparator = None
    
    ## TODO: this has to be optimized. This data can be extracted in one query, 
    ## having compared_user and user rating for each film in one row       
            
    # for new users get all their ratings            
    if new_user:        
        # new comparator
        comparator = RatingComparator()
        comparator.main_user = curuser
        comparator.compared_user = compared_user
        
        curuser_ratings = Rating.objects.filter(         
            user=compared_user.id, 
            type=Rating.TYPE_FILM,
            rating__isnull=False            
        )   
    # for old users (that we have comparators with) get only
    else:        
        # get old comparator
        try:
            comparator = RatingComparator.objects.get(main_user=curuser.id, compared_user=compared_user.id)
            films_compared = comparator.common_films
            oryg_films_compared = comparator.common_films
            sum_difference = comparator.sum_difference
            
            ddebug('Fetched: ' + unicode(comparator))
            
            # this means not set
            if sum_difference == -1:
                sum_difference = oryg_films_compared * comparator.score
                ddebug('Re-computed sum difference: ' + unicode(sum_difference))
            
        except RatingComparator.DoesNotExist:
            debug("FATAL ERROR!!! CANNOT GET COMPARATOR FOR USERS: " + unicode(curuser.username) + " and " + unicode(compared_user.username))
            debug("Creating new one... but this is WRONG!!!")
            comparator = RatingComparator()
            comparator.main_user = curuser
            comparator.compared_user = compared_user       

    ratings1 = rating_helper.get_user_ratings(curuser)
    ratings2 = rating_helper.get_user_ratings(compared_user)

    common_films = set(ratings1.keys()).intersection(ratings2.keys())
    sum_difference = sum(abs(ratings1[id]-ratings2[id]) for id in common_films)
    films_compared = len(common_films)
    if True:
        ddebug('Films compared: ' + unicode(films_compared))
        ddebug('Accum. difference: ' + unicode(sum_difference))
        
        if oryg_films_compared != films_compared:
            if films_compared > MIN_FILMS_COMPARED:
                the_score = Decimal(sum_difference)/Decimal(films_compared)
                comparator.score = the_score
                comparator.common_films = films_compared        
                comparator.sum_difference = sum_difference
                # save every other time to make sure that we always update both comparators (user1 vs user2 and user2 vs user1)
                # THIS IS NOT NECESSARY ANYMORE (we only need to do it once)
    #            if comparator.previous_save_date:
    #                comparator.previous_save_date = None
    #            else:
    #                comparator.previous_save_date = comparator.updated_at
                
                comparator.previous_save_date = None            
                comparator.save()
            
                # create/update the other object
                try:
                    other_comparator = RatingComparator.objects.get(main_user=compared_user.id, compared_user=curuser.id)                
                    ddebug('Fetched the other comparator: ' + unicode(comparator))                                
                except RatingComparator.DoesNotExist:            
                    ddebug("Creating the other comparator")
                    other_comparator = RatingComparator()
                    other_comparator.main_user = compared_user
                    other_comparator.compared_user = curuser
                other_comparator.score = comparator.score
                other_comparator.common_films = comparator.common_films
                other_comparator.sum_difference = comparator.sum_difference
                other_comparator.previous_save_date = comparator.previous_save_date
                
                other_comparator.save()
            
                debug("Updated ratings between: " + unicode(curuser) + ", " + unicode(compared_user) + "[" + unicode(comparator.score) + "]") 
            else:
                ddebug("Too few common films ("+unicode(films_compared)+") between users: " + unicode(curuser) + ", " + unicode(compared_user))
        else:
            ddebug("No new films to be compared between users: " + unicode(curuser) + ", " + unicode(compared_user))

class OverallFilmRating:
    avg = None
    count = None
        
def get_average_rating_for_film(film, type):
    
#    qset_average = (
#            Q(film=film) &
#            Q(type=type) &
#            Q(rating__isnull=False)
#        )
#    avg = Rating.objects.filter(qset_month).avg("rating") 
        
    query = """
        SELECT avg(rating), count(*)
        FROM core_rating
        WHERE film_id=%(film_id)s
            AND type=%(type)s
            AND rating IS NOT NULL
        """ % {
            'film_id': film.id,
            'type': type
        }

    cursor = connection.cursor()
    cursor.execute(query)
    
    overall_film_rating = OverallFilmRating()
    for row in cursor.fetchall():
        overall_film_rating.avg = row[0]
        overall_film_rating.count = row[1]
   
    cursor.close()
    # http://www.mail-archive.com/django-users@googlegroups.com/msg92582.html
    connection._rollback()
 
    return overall_film_rating
    
def do_update_films_popularity():
    """
        Goes through all movies ever rated and checks their ratings, 
        updating the popularity and popularity_month columns in core_film
        as well as computing average ratings and counts for each type
        in core_filmranking 
    """
    
    today = date.today()
    last_month = today - timedelta(days=30)
    yesterday = today - timedelta(days=1)
    
    debug("Film monthly popularity to be computed for time between " + unicode(last_month) + " and " + unicode(today))
        
    q_only_rated = (
            Q(rating__last_rated__gt=yesterday) &
            Q(rating__rating__isnull=False)
        )    
    all_films = Film.objects.filter(q_only_rated)    
    all_films = all_films.distinct()
    all_count = all_films.count()
    
    debug("Popularity to be computed for " + unicode(all_count) + " films")
    
    for film in all_films:
        
        # compute overall popularity
        qset = (
            Q(film=film) &
            Q(type=Rating.TYPE_FILM) &
            Q(rating__isnull=False)
        )
        popularity = Rating.objects.filter(qset).count()

        # compute monthlypopularity
        qset_month = (
            Q(film=film) &
            Q(type=Rating.TYPE_FILM) &
            Q(last_rated__gt=last_month) &
            Q(rating__isnull=False)
        )
        popularity_month = Rating.objects.filter(qset_month).count()
                
        """
        # compute average ratings for each type
        for type_obj in Rating.ALL_RATING_TYPES:            
            type = type_obj[0]                       
            overall_film_rating = get_average_rating_for_film(film, type)      
            avg = overall_film_rating.avg
            cnt = overall_film_rating.count
                       
            try:
                qset_ranking = (
                    Q(film=film) &
                    Q(type=type)                
                )
                ranking = FilmRanking.objects.get(qset_ranking)
                ddebug("Ranking for film " + unicode(film.title) + " type " + unicode(type) + " retrieved.")            
            except FilmRanking.DoesNotExist:
                ranking = FilmRanking()
                ranking.film = film
                ranking.type = type
                ddebug("Ranking for film " + unicode(film.title) + " type " + unicode(type) + " created.")
                       
            if (avg!=None):
                if (float(avg)>0):
                    ranking.average_score = avg
                    ranking.number_of_votes = cnt
                    ddebug("Ranking for film " + unicode(film.title) + " type " + str(type) + " saved (" + str(ranking.average_score) + ").")
                    ranking.save()
                else:   
                    ddebug("Ranking for film " + unicode(film.title) + " type " + unicode(type) + " not saved (" + unicode(avg) + ").")
                    return      
            else:
                ddebug("Ranking for film " + unicode(film.title) + " type " + unicode(type) + " not saved (" + unicode(avg) + ").")        
        """
        do_update = False
        if not (film.popularity == popularity):
            ddebug(unicode(film) + " popularity set to " + unicode(popularity))
            film.popularity = popularity
            if False and popularity >= 10 and settings.RECOMMENDATIONS_ENGINE == 'film20.new_recommendations.recommendations_engine':
                from film20.recommendations import engine
                if hasattr(engine, 'compute_film_features'):
                    engine.compute_film_features(film, save=True, initial_only=True)

            do_update = True
        if not (film.popularity_month == popularity_month):            
            ddebug(unicode(film) + " popularity_month set to " + unicode(popularity_month))               
            film.popularity_month = popularity_month
            do_update = True            
        if do_update:
            film.save()
        
    debug("Film monthly popularity computed for time between " + unicode(last_month) + " and " + unicode(today))
    
    return
    
def do_update_persons_popularity():
    """
        Goes through all persons and checks their ratings, 
        updating the popularity and popularity_month columns
    """

    today = date.today()
    last_month = today - timedelta(days=30)
        
    all_persons = Person.objects.all()
    for person in all_persons:
        if person.is_actor:
            do_update_single_person(person, Rating.TYPE_ACTOR, last_month)
        if person.is_director:
            do_update_single_person(person, Rating.TYPE_DIRECTOR, last_month)
        
    debug("Person monthly popularity computed for time between " + unicode(last_month) + " and " + unicode(today))
    
    return

def do_update_single_person(person, type, last_month):
    if type==Rating.TYPE_ACTOR:
        q_actor_director = Q(actor=person)
    else:
        q_actor_director = Q(director=person)
        
    qset = (
        q_actor_director &
        Q(type=type) &
        Q(rating__isnull=False)
    )
    popularity = Rating.objects.filter(qset).count()

    qset_month = (
        q_actor_director &
        Q(type=type) &
        Q(last_rated__gt=last_month) &
        Q(rating__isnull=False)
    )
    popularity_month = Rating.objects.filter(qset_month).count()
       
    do_update = False     
    if type==Rating.TYPE_ACTOR:
        if not (person.actor_popularity == popularity):
            ddebug(unicode(person) + " popularity set to " + unicode(popularity))
            person.actor_popularity = popularity
            do_update = True
        if not (person.actor_popularity_month == popularity_month):            
            ddebug(unicode(person) + " popularity_month set to " + unicode(popularity_month))               
            person.actor_popularity_month = popularity_month
            do_update = True
    else:
        if not (person.director_popularity == popularity):
            ddebug(unicode(person) + " popularity set to " + unicode(popularity))
            person.director_popularity = popularity
            do_update = True
        if not (person.director_popularity_month == popularity_month):            
            ddebug(unicode(person) + " popularity_month set to " + unicode(popularity_month))               
            person.director_popularity_month = popularity_month
            do_update = True                        
    if do_update:
        person.save()

def get_films_for_computing_scores(last_day=True):
    today = datetime.today()
    yesterday = today - timedelta(1)
    
    # only rated last day (default)
    if last_day: 
        q_rating = (
            Q(film_ratings__last_rated__gte = yesterday)
            & Q(film_ratings__type = Rating.TYPE_FILM)
        )
    # all time
    else:
        q_rating = (
            Q(film_ratings__last_rated__isnull = False)
            & Q(film_ratings__type = Rating.TYPE_FILM)
        )
    films = Film.objects.filter(q_rating).distinct()
    return films
    
def refresh_score_to_recom():
    update_query = """
            update core_ratingcomparator set score_to_recom = 5 - (score / 0.5)
            """ 
    cursor = connection.cursor()
    cursor.execute("BEGIN")
    cursor.execute(update_query)    
    cursor.execute("COMMIT")
    cursor.close()

def do_compute_probable_scores(last_day=True, only_new_users=False):
    """
        Compute probable scores for all users 
    """

#    refresh_( 5 - (score / 0.5) )()
#    debug ("Score_to_recom refreshed")
    
    today = datetime.today()
    yesterday = today - timedelta(1)
    last_two_months = today - timedelta(60)
       
    if only_new_users:
        debug("Computing scores for users that rated some film after "+str(yesterday))
        users = User.objects.all()
        users = users.extra(
            where = ["id IN (select distinct user_id from core_rating where rating is not null and last_rated>'%s')" % yesterday]
        )
    else:
        debug ("Computing scores for all users")
        users = User.objects.all()       

    # for all users
    users_computed = 0
    for curuser in users:
        compute_probable_scores_for_user(curuser)        
        users_computed = users_computed + 1 
        
    debug ("Scores computed " + unicode(users_computed) + " users.")
    
    return

def compute_probable_scores_for_user(user):
    """
        Compute probable scores for a particular user
        Currently only considers main rating for films
    """

    update_query = """
        UPDATE core_rating 
        SET guess_rating_alg1 = summary.guess_rating, number_of_ratings=summary.sum_objects_real                                                                            
        FROM 
            (SELECT a.parent_id, a.guess_rating, a.sum_objects_real 
            FROM 
                (SELECT core_rating.parent_id, 
                    (sum(rating*( 5 - (score / 0.5) ))/sum(( 5 - (score / 0.5) ))) as guess_rating, 
                    count(*) as sum_objects_real 
                FROM "core_rating" , "core_ratingcomparator" 
                WHERE "core_rating"."type" = %(type)s 
                    AND "core_rating"."rating" IS NOT NULL 
                    AND "core_rating"."actor_id" IS NULL 
                    AND "core_rating"."director_id" IS NULL 
                    AND core_ratingcomparator.compared_user_id=%(user)s 
                    AND core_ratingcomparator.main_user_id=core_rating.user_id 
                    AND core_ratingcomparator.score<=%(min_score)s group by core_rating.parent_id having sum(( 5 - (score / 0.5) ))>0) a 
            WHERE a.sum_objects_real>=%(min_common_films)s) as summary
        WHERE core_rating.parent_id = summary.parent_id AND core_rating.user_id=%(user)s AND core_rating.type=%(type)s
    """ % {            
        'user': user.id,
        'type': Rating.TYPE_FILM,
        'min_score': RatingComparator.MIN_COMMON_TASTE,
        'min_common_films': RatingComparator.MIN_COMMON_FILMS
    }
    insert_query = """
        INSERT INTO core_rating(type, parent_id, film_id, user_id, guess_rating_alg1, number_of_ratings)
        (
            
            SELECT 1, summary.parent_id, summary.parent_id, %(user)s, summary.guess_rating, summary.sum_objects_real FROM
            
            (
            SELECT a.parent_id, a.guess_rating, a.sum_objects_real FROM (
            SELECT core_rating.parent_id, (sum(rating*( 5 - (score / 0.5) ))/sum(( 5 - (score / 0.5) ))) as guess_rating, count(*) as sum_objects_real
            FROM "core_rating", "core_ratingcomparator" 
            WHERE "core_rating"."type" = %(type)s  
                    AND "core_rating"."rating" IS NOT NULL 
                    AND "core_rating"."actor_id" IS NULL 
                    AND "core_rating"."director_id" IS NULL 
                    AND core_ratingcomparator.compared_user_id=%(user)s
                    AND core_ratingcomparator.main_user_id=core_rating.user_id 
                    AND core_ratingcomparator.score<=%(min_score)s group by core_rating.parent_id having sum(( 5 - (score / 0.5) ))>0) a 
            WHERE a.sum_objects_real>=%(min_common_films)s
            ) as summary
            WHERE parent_id NOT IN (select parent_id from core_rating where user_id=%(user)s AND type=%(type)s)
            
        )""" % {            
        'user': user.id,
        'type': Rating.TYPE_FILM,
        'min_score': RatingComparator.MIN_COMMON_TASTE,
        'min_common_films': RatingComparator.MIN_COMMON_FILMS
    }
                
    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute(update_query)    
        cursor.execute(insert_query)
        cursor.execute("COMMIT")
        debug ("Scores computed for user: " + unicode(user))
    except Exception, e:
        debug("Error (probably division by zero. To be fixed in: http://jira.filmaster.org/browse/FLM-73). Continuing...")
        debug(e)
        debug ("Scores NOT computed for user: " + unicode(user))
    cursor.close()
    
    # TODO: return rows affected for both 
    return -1

def fetch_synopses_for_recently_imported_films(fetcher=DEFAULT_FETCHER):
    today = datetime.today()
    yesterday = today - timedelta(1)

    query = (
        Q(importedfilm__created_at__isnull = False) & 
        Q(importedfilm__created_at__gte = yesterday) 
    )

    all_films = Film.objects.filter(query).order_by("-importedfilm__created_at").distinct()
    fetch_synopses_for_films(all_films, fetcher=fetcher)

def fetch_synopses_for_recently_imported_films_no_synopsis(fetcher=DEFAULT_FETCHER):
    today = datetime.today()
    yesterday = today - timedelta(1)

    query = (
        Q(importedfilm__created_at__isnull = False) & 
        Q(importedfilm__created_at__gte = yesterday) & 
        ( ( Q(filmlocalized__fetched_description__isnull = True)
        & Q(filmlocalized__LANG = LANGUAGE_CODE) ) | Q(filmlocalized__isnull = True) )
    )

    all_films = Film.objects.filter(query).order_by("-importedfilm__created_at").distinct()
    fetch_synopses_for_films(all_films, fetcher=fetcher)

def fetch_synopses_for_films_no_localized_film(offset=0, number=None):
    query = (
        Q(filmlocalized__isnull = True)
    )

    if number:
        all_films = Film.objects.filter(query).order_by("-popularity").distinct()[offset:number]
    else:
        all_films = Film.objects.filter(query).order_by("-popularity").distinct()
    fetch_synopses_for_films(all_films)

def fetch_synopses_for_films_no_synopses(offset=0, number=None):
    query = (
        ( Q(filmlocalized__fetched_description__isnull = True) &
          Q(filmlocalized__description__isnull = True)
        & Q(filmlocalized__LANG = LANGUAGE_CODE) )
    )
    if number:
        all_films = Film.objects.filter(query).order_by("-popularity").distinct()[offset:number]
    else:
        all_films = Film.objects.filter(query).order_by("-popularity").distinct()
    fetch_synopses_for_films(all_films)

def fetch_synopses_for_films(all_films, fetcher=DEFAULT_FETCHER):
    not_found = 0
    found = 0
    
    for film in all_films:
        the_title = film.title
        synopses = get_synopses(the_title, film.release_year, fetcher_type=fetcher)
        if not synopses:
            ddebug("Cannot find synopsis for film " + unicode(film.permalink))
            localized_title = film.get_localized_title()

            # in case the localized title is empty, just treat it as a null
            if localized_title.strip() == "":
                localized_title = None 
            if localized_title != None:
                synopses = get_synopses(localized_title, film.release_year, fetcher_type=fetcher)
                if not synopses:
                    ddebug("Cannot find synopsis for film (localized title) " + unicode(film.permalink))
                    not_found = not_found + 1
                    continue
            else:
                not_found = not_found + 1
                continue

        if synopses:
            debug("Synopsis found for film " + unicode(film.permalink))
            found = found + 1            

            film_localized = film.get_or_create_film_localized(LANGUAGE_CODE)
                
            film_localized.fetched_description = synopses[0]['synopsis'][0:15000]
            film_localized.fetched_description_url = synopses[0]['url']                
            film_localized.fetched_description_url_text = synopses[0]['author']

            if 'title' in synopses[0]:
                film_localized.title = synopses[0]["title"]

            if synopses[0]['distributor']:
                film_localized.fetched_description_type = FilmLocalized.DESC_DISTRIBUTOR
            else:
                film_localized.fetched_description_type = FilmLocalized.DESC_USER
            film_localized.save() 
                                       
    debug("Total found: " + unicode(found))           
    debug("Total not found: " + unicode(not_found))

MIN_FILM_RATES = settings.RECOMMENDATIONS_MIN_VOTES_FILM
MIN_USER_RATES = settings.RECOMMENDATIONS_MIN_VOTES_USER

def prepare_data(last_day=True, only_new_users=False):
    """
        Process the data and queries for an algorithm counting Recommendations and User similiarity
    """
    log = open("temp_data/new_recom.log", "w")
    adress = "film20/recommendations/bot_helper.prepare_data: "
    users = User.objects.all().order_by('id')
    films = Film.objects.all()
    users_id = [user.id for user in users]
    films_id = [film.id for film in films]
    
    # save data for algorithm
    user_map, film_map = {}, {}
    userMapFile = open("temp_data/userMap.in","w")
    cnt=0
    for usr in users_id:
        user_map[usr] = cnt
        userMapFile.write(repr(usr)+'\n')
        cnt += 1
    log.write(adress+"made user_map\n")
    userMapFile.close();
    
    filmMapFile = open("temp_data/filmMap.in","w")
    cnt = 0
    for flm in films_id:
        film_map[flm] = cnt
        filmMapFile.write(repr(flm)+'\n')
        cnt += 1
    log.write(adress+"made film_map\n")
    filmMapFile.close();
    
    ratings=[] # list of rating containing user, film, rating, and actual predicted rating
    for usr in users:
        query= Rating.objects.filter(type=Rating.TYPE_FILM, director__isnull=True, actor__isnull=True, rating__isnull=False, user=usr ).values("parent", "rating")
        for rat in query:
            ratings.append([usr.id, rat['parent'], rat['rating']])
    log.write(adress+"got ratings\n")
    
    for rat in ratings:
        if rat[0] not in user_map or rat[1] not in film_map:
            ratings.remove(rat)
    
    ratfile = open("temp_data/ratings.in", "w")
    ratfile.write(repr(len(ratings)) + ' ' + repr(len(users_id)) + \
            ' ' + repr(len(films_id)) + ' ' + repr(MIN_USER_RATES) + ' ' + \
            repr(MIN_FILM_RATES) + '\n')
    for rat in ratings:
        ratfile.write(repr(user_map[rat[0]])+' '+repr(film_map[rat[1]])+' '+repr(rat[2])+'\n')
    ratfile.close()
    log.write(adress+"ratings written\n")
    # koniec zapisywania
    
    return; 
    
def compute_probable_scores_for_user2(user):
    """
        Computes recommendations for user 
    """
    subprocess.call(["mkdir","temp_data"])
    subprocess.call(["g++","count_recommendations.cpp","-ocount_recommendations","-O2"])
    log = open("temp_data/new_recom.log", "w")
    adress = "film20/recommendations/bot_helper.compute_probable_scores_for_user2: "
    users = User.objects.all()
    films = Film.objects.all()
    users_id = [user.id for user in users]
    films_id = [film.id for film in films]
    ratings=[] # list of rating containing user, film, rating, and actual predicted rating
    for usr in users:
        query= Rating.objects.filter(type=Rating.TYPE_FILM, director__isnull=True, actor__isnull=True, rating__isnull=False, user=usr ).values("parent", "rating")
        print(usr)
        for rat in query:
            ratings.append([usr.id, rat['parent'], rat['rating'], 5.0])
    log.write(adress+"got ratings\n")
    
    # save data for algorithm
    user_map, film_map = {}, {}
    cnt=0
    for usr in users_id:
        user_map[usr] = cnt
        cnt += 1
    log.write(adress+"made user_map\n")
    
    cnt = 0
    for flm in films_id:
        film_map[flm] = cnt
        cnt += 1
    log.write(adress+"made film_map\n")
    for rat in ratings:
        if rat[0] not in user_map or rat[1] not in film_map:
            ratings.remove(rat)
    
    ratfile = open("temp_data/ratings.in", "w")
    ratfile.write(repr(len(ratings))+' '+repr(len(users_id))+' '+repr(len(films_id))+'\n')
    for rat in ratings:
        ratfile.write(repr(user_map[rat[0]])+' '+repr(film_map[rat[1]])+' '+repr(rat[2])+'\n')
    ratfile.close()
    log.write(adress+"ratings written\n")
    #save queries
    queries =[]
    query=Rating.objects.filter(type=Rating.TYPE_FILM, director__isnull=True, actor__isnull=True, user=user,  film__popularity__gte=MIN_RATINGS).values("parent", "user", "id")
    for rat in query:
        queries.append(['r', rat['user'], rat['parent'], rat['id']])
            
    for q in queries:
        if q[1] not in user_map or q[2] not in film_map:
            queries.remove(q)
        
    quw = open("temp_data/queries.in", "w")    
    quw.write(repr(len(queries))+'\n')
    for query in queries:
        quw.write(query[0]+' '+repr(user_map[query[1]])+' '+repr(film_map[query[2]])+' '+repr(query[3])+' '+repr(query[1])+' '+repr(query[2])+'\n')
    quw.close()
    log.write(adress+"queries written\n")
    log.close()
    subprocess.call(["./count_recommendations"])
    #subprocess.call(["psql","-U"+DATABASE_USER,DATABASE_NAME,"-ftemp_data/data_update.sql"])
    # koniec zapisywania
    return -1; 

def fix_film_ids_for_activities():
    from film20.useractivity.models import UserActivity
    query = (
        Q(activity_type = 1)
    )

    all_activities = UserActivity.objects.filter(query)
    for activity in all_activities:
        try:
            film_id = None
            for film in activity.post.related_film.all():
                film_id = film.id
            if film_id != None:
                related_films = Film.objects.filter(id=film_id)
                activity.film = related_films[0]
                activity.save()
                print "Saved film for activity: " + str(activity.film)
            else:
                print "No film connected with review: " + str(activity.post.id)
        except Exception, e:
            print e

def debug(str):
    if DEBUG == True:
        if DEBUG_USING_LOGGING:
            logger.info(unicode(str))
        else:
            print("[DEBUG] " + unicode(str))

def ddebug(str):
    if DEBUG_DETAILED == True:
        if DEBUG_USING_LOGGING:
            logger.debug(unicode(str))
        else:
            print("[DDEBUG] " + unicode(str))

CHUNK_SIZE = 20000
POPULAR_FILMS_NUMBER = 200
RELIABILITY_BAR = 30.0
FILM_RELIABILITY_BAR = 80.0
USER_RELIABILITY_BAR = 100.0
AVERAGE_RATE = 6.88
AVERAGE_WEIGHT = 0.2
FILM_WEIGHT = 0.2
USER_WEIGHT = 0.1
TAG_INFLUENCE = Decimal('0.1')
DIRECTOR_INFLUENCE = Decimal('0.2')
ACTOR_INFLUENCE = 0.03
MAX_DIFFERENCE = 4.5
RATING_EXPONENT = 3
RATING_INFLUENCE = 0.25 / pow(MAX_DIFFERENCE, RATING_EXPONENT)

def count_guessed_rate(user, film):
    ratings = Rating.get_user_ratings(user)
    logger.info("counting guessed rate for film %d", film.id)

    if len(ratings) < MIN_USER_RATES:
        return None

    average_rate, average_weight = AVERAGE_RATE, AVERAGE_WEIGHT

    film_weight = 0.0
    film_rate = film.average_score() or 0.0
    film_rate = float(film_rate)

    if film_rate:
        film_weight = FILM_WEIGHT * pow(
                float(film.number_of_votes() / FILM_RELIABILITY_BAR), 0.3)

    user_rate = sum(ratings.values()) / len(ratings)
    user_weight = USER_WEIGHT * (len(ratings) / USER_RELIABILITY_BAR) ** 0.3

#    film_ids = ratings.keys()
#    scores = dict(FilmComparator.objects.filter(
#            main_film=film, compared_film__id__in=film_ids).\
#            values_list('compared_film', 'score'))

    key = cache.Key("compared_films", film.id)
    scores = cache.get(key)
    if scores is None:
        query = FilmComparator.objects.filter(main_film=film).values_list(
                    'compared_film', 'score')
        scores = dict((f, float(s)) for (f, s) in query)
        cache.set(key, scores)


    sum_weights = 0.0
    sum_rate = 0.0
    for film_id, rating in ratings.items():
        if film_id in scores:
            weight = float(scores[film_id])
            sum_weights += weight
            sum_rate += float(rating) * weight

    sum_rate += film_weight * film_rate + user_weight * user_rate
    sum_rate += average_weight * average_rate
    sum_weights += film_weight + user_weight + average_weight
    recommendation = None
    if sum_weights > 0.0 and sum_rate >= 0.0:
        score = Decimal(str(sum_rate / sum_weights))
        if score <= 10:
            recommendation, created = Recommendation.objects.get_or_create(
                user=user, 
                film=film,
                defaults=dict(guess_rating_alg2=score),
            )
            if not created:
                recommendation.guess_rating_alg2 = score
                recommendation.save()
    # transaction.commit()
    return recommendation

def commit(create_command):
    cursor = connection.cursor()
    cursor.execute(create_command)
    transaction.commit_unless_managed()


def init_loading_comparators(sql_file):
    """Initializes proccess of loading FilmComparators to the database."""

    sql_file.write("DROP TABLE core_filmcomparator_temp;\n")
    # Creates temp table for FilmComparators
    sql_file.write("CREATE TABLE core_filmcomparator_temp(id serial " + \
          "NOT NULL PRIMARY KEY, main_film_id integer, compared_film_id " + \
          "integer, score numeric(4, 3));\n")

def finish_loading_comparators(sql_file):
    """Finishes the process of creating comparators."""

    sql_file.write("CREATE INDEX core_filmcomparator_main_film_id_temp ON " + \
          "core_filmcomparator_temp(main_film_id);\n")
    sql_file.write("CREATE INDEX core_filmcomparator_compared_film_id_temp ON " + \
          "core_filmcomparator_temp(compared_film_id);\n")

    sql_file.write("ALTER TABLE core_filmcomparator_temp ADD FOREIGN KEY" + \
          "(main_film_id) REFERENCES core_film(parent_id);\n")
    sql_file.write("ALTER TABLE core_filmcomparator_temp ADD FOREIGN KEY " + \
          "(compared_film_id) REFERENCES core_film(parent_id);\n")

    sql_file.write("DROP TABLE core_filmcomparator;\n")
    sql_file.write("ALTER TABLE core_filmcomparator_temp_id_seq RENAME TO " + \
          "core_filmcomparator_seq;\n")
    sql_file.write("ALTER TABLE core_filmcomparator_temp RENAME TO " + \
          "core_filmcomparator;\n")

    sql_file.write("ALTER INDEX core_filmcomparator_main_film_id_temp " + \
          "RENAME TO core_filmcomparator_main_film_id;\n")
    sql_file.write("ALTER INDEX core_filmcomparator_compared_film_id_temp " + \
          "RENAME TO core_filmcomparator_compared_film_id;\n")


def create_comparators(comparators):
    """Loads comparators to the database."""

    sql_file = open('load_data.sql', 'w')

    init_loading_comparators(sql_file)

    comparators.sort()
    sql_file.write("COPY core_filmcomparator_temp (main_film_id, " + \
            "compared_film_id, score) FROM stdin;\n")

    prev = (comparators[0][0], comparators[0][1])
    score = Decimal('0.0')
    for f1, f2, v in comparators:
        if (f1, f2) != prev:
            sql_file.write("%d\t%d\t%F\n" % (prev[0], prev[1], score))
            score = Decimal('0.0')
            prev = (f1, f2)
        score += v

    sql_file.write("%d\t%d\t%F\n" % (prev[0], prev[1], score))
    sql_file.write("\\.\n")

    finish_loading_comparators(sql_file)
    sql_file.close()

def add_tag_influence(comparators):
#    from itertools import product

    tags = Tag.objects.all()
    for tag in tags:
        films = [flm.film.id for flm in TaggedItem.objects.get_by_model(
                FilmLocalized.objects.all(), tag)]
        #For python2.6
        #comparators += list(product(films, films, [TAG_INFLUENCE]))

        comparators += \
            [(f1, f2, TAG_INFLUENCE) for f1 in films for f2 in films]

def add_directors_influence(comparators):
#    from itertools import product

    directors = Person.objects.filter(is_director=True)
    for director in directors:
        films = [flm['id'] for flm in list(
                        director.films_directed.all().values('id'))]
        #For python2.6
        #comparators += list(product(films, films, [DIRECTOR_INFLUENCE]))

        comparators += \
            [(f1, f2, DIRECTOR_INFLUENCE) for f1 in films for f2 in films]

def count_comparator(film1, film2, actors, ratings):

    score = 0.0
    actors1 = actors[film1.id]
    actors2 = actors[film2.id]
    ratings1 = ratings[film1.id]
    ratings2 = ratings[film2.id]
    users = set(ratings1.keys()) & set(ratings2.keys())
    for user in users:
        score += MAX_DIFFERENCE - float(abs(ratings1[user] - ratings2[user]))
    if len(users) > 0:
        score /= float(len(users))
        score = pow(score, RATING_EXPONENT)
        score *= RATING_INFLUENCE
        score *= pow(float(len(users)) / RELIABILITY_BAR, 0.33)
    score += ACTOR_INFLUENCE * float(len(actors1 & actors2))
    return Decimal(str(score))

def add_popular_films(comparators):

    films = list(Film.objects.filter(
                filmranking__number_of_votes__gte=300).distinct())
    popular_films = []
    for film in films:
        popular_films.append((film.filmranking_set.all().order_by(
                "-number_of_votes").values('number_of_votes')[0], film))
    popular_films.sort(reverse=True)
    popular_films = popular_films[:POPULAR_FILMS_NUMBER]

    films = list(Film.objects.filter(
                filmranking__number_of_votes__gte=MIN_FILM_RATES).distinct())

    film_helper = FilmHelper()
    film_actors = {}
    film_ratings = {}

    for film in films:
        film_ratings[film.id] = {}

    ratings = list(Rating.objects.filter(type=Rating.TYPE_FILM,
            rating__isnull=False).values('user', 'film', 'rating'))

    for rat in ratings:
        if rat['film'] in film_ratings:
            film_ratings[rat['film']][rat['user']] = rat['rating']

    for film in films:
        film_actors[film.id] = set([c['person'] for c in
            film_helper.get_film_actors(film, limit=20).values('person')])

    for film2 in popular_films:
        for film1 in films:
            comparators.append((film1.id, film2[1].id,
                count_comparator(film1, film2[1],
                    film_actors, film_ratings)))
import sys
def compute_film_comparators(lang='pl'):
    """ Recomputes FilmComparators. """

    comparators = []
    add_tag_influence(comparators)
    add_directors_influence(comparators)
    add_popular_films(comparators)
    create_comparators(comparators)

from film20.notification import models as notification
from django.core.urlresolvers import reverse

def compute_fast_recommendations(user_id, send_notice=True):
    from recom_helper import RecomHelper
    from film20.core.models import Recommendation
    from film20.showtimes.showtimes_helper import get_films
    from film20.showtimes.models import Channel
    from film20.showtimes.utils import get_today
    from itertools import chain
    import pytz

    helper = RecomHelper()
    
    user = User.objects.get(pk=user_id)
    profile = user.get_profile()

    for r in helper.get_ranking()[:settings.FAST_RECOMMENDATIONS_NUMBER_OF_TOP_FILMS]:
        count_guessed_rate(user, r.film)

    profile.recommendations_status = profile.FAST_RECOMMENDATIONS
    profile.save()

    from film20.core.deferred import defer
    defer(compute_fast_recommendations_phase2, user_id, send_notice)

def compute_fast_recommendations_phase2(user_id, send_notice):
    from recom_helper import RecomHelper
    from film20.core.models import Recommendation
    from film20.showtimes.showtimes_helper import get_films
    from film20.showtimes.models import Channel
    from film20.showtimes.utils import get_today
    from itertools import chain
    import pytz

    helper = RecomHelper()
    
    user = User.objects.get(pk=user_id)
    profile = user.get_profile()

    if profile.country in settings.COUNTRIES_WITH_SHOWTIMES:
        if profile.timezone_id:
            timezone = pytz.timezone(profile.timezone_id)
        else:
            timezone = pytz.utc
            logger.warning("user %r has no timezone, using utc", user)
        
        today = get_today(timezone)

        theaters = Channel.objects.selected_by(user, Channel.TYPE_CINEMA)
        tv_channels = Channel.objects.selected_by(user, Channel.TYPE_TV_CHANNEL)
        for i in range(3):
            date = today + timedelta(days=i)
            for channels in (theaters, tv_channels):
                for film in get_films(date, channels):
                    count_guessed_rate(user, film)
    
    if send_notice:
        notification.send([user], 'recommendations_fast_calculated', {})

def send_recommendations_calculated_notices():
    from film20.core.models import Profile

    for profile in Profile.objects.filter(recommendations_status=1, recommendations_notice_sent=0):
        notification.send([profile.user], 'recommendations_calculated', {})
        profile.recommendations_notice_sent = 1
        profile.save()
