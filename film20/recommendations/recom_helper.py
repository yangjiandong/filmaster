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
from django.utils.translation import gettext_lazy as _
from random import *

from datetime import datetime
from datetime import date
from datetime import timedelta

from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from film20.tagging.utils import parse_tag_input

from film20.core.models import Film
from film20.core.models import Rating
from film20.core.models import RatingComparator
from film20.core.models import FilmRanking
from film20.core.models import Recommendation
from film20.core.models import ObjectLocalized
from film20.filmbasket.models import BasketItem

from film20.recommendations.models import Computed
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

from film20.utils import cache

import film20.settings as settings
# constants
RECOMMENDATION_ALGORITHM = getattr(settings, "RECOMMENDATION_ALGORITHM", "alg1")

import logging
logger = logging.getLogger(__name__)

FILMASTERS_ALL = 'all'
FOLLOWING_ONLY = 'following'
FOLLOWERS_ONLY = 'followers'

FILMASTER_TYPES = (
    (FILMASTERS_ALL, _('all Filmasters')),
    (FOLLOWING_ONLY, _('following only')),
    (FOLLOWERS_ONLY, _('followers only')),
)

FILMASTERS_SORT_COMMON_TASTE = 'common_taste'
FILMASTERS_SORT_COMMON_FILMS = 'common_films'
FILMASTERS_SORT_NAME = 'username'
FILMASTERS_DATE_JOINED = 'date_joined'
FILMASTERS_DISTANCE = 'distance'

FILMASTERS_SORT_BY = (
    (FILMASTERS_SORT_COMMON_TASTE, _('common taste')),
    (FILMASTERS_SORT_COMMON_FILMS, _('number of common films')),
    (FILMASTERS_SORT_NAME, _('user name')),
    (FILMASTERS_DATE_JOINED, _('date joined')),
)

class RecomHelper:

    def _perform_queries(self, query_with_tags):
        select_query = query_with_tags['select'] if query_with_tags['select'] is not None else ''
        from_query = query_with_tags['from'] if query_with_tags['from'] is not None else ''
        join_query = query_with_tags['join'] if query_with_tags['join'] is not None else ''
        where_query = query_with_tags['where'] if query_with_tags['where'] is not None else ''
        order_by = query_with_tags['order_by'] if query_with_tags['order_by'] is not None else ''

        query = select_query + from_query + join_query + where_query + order_by
        params = query_with_tags['params']
        return query, params

    def __execute_film_queries(self, query, params):
        query = Film.objects.raw(query, params)
#        query = list(query)
        return query

    def __execute_rating_queries(self, query, params):
        query = Rating.objects.raw(query, params)
#        query = list(query)
        return query

    def get_recently_popular_films_query(self, user_id=None, rated_films=None, tags=None, year_from=None, year_to = None, related_director = None, related_actor = None, popularity = None, limit = 100, **kw):
        """
            Gets the X most popular movies and removes the movies recently viewed by the user (in session)
            Removes those in basket and those ever rated
        """
   
        if RECOMMENDATION_ALGORITHM == "alg1":
            guess_rating=', "core_rating"."guess_rating_alg1" AS "guess_rating"'
            join_query = ''
        elif RECOMMENDATION_ALGORITHM == "alg2":
            guess_rating=', "core_recommendation"."guess_rating_alg2" AS "guess_rating"'
            join_query = ' LEFT OUTER JOIN "core_recommendation" ON ("core_recommendation"."film_id" = "core_film"."parent_id" AND "core_recommendation"."user_id" = %(user_id)s)'
        else:
            guess_rating=''
            join_query = ''

        # exclude all in session
        excluded = ''
        if rated_films:
            excluded = 'NOT "core_film"."parent_id" IN ('
            for film in rated_films:
                excluded += str(film) + ', '
            excluded = excluded[:-2]
            excluded += ') AND '

        select_query='SELECT DISTINCT "core_object".*, "core_film".*'
        from_query=' FROM "core_film" '
        join_query = ' INNER JOIN "core_object" ON ("core_film"."parent_id" = "core_object"."id") LEFT OUTER JOIN "core_rating" ON ("core_film"."parent_id" = "core_rating"."parent_id" AND "core_rating"."user_id" = %(user_id)s) '
        where_query=' WHERE ' + excluded + ' "core_film"."parent_id" IN (SELECT "parent_id" FROM "core_film" EXCEPT SELECT "film_id" FROM "filmbasket_basketitem" WHERE "wishlist" IS NOT NULL AND "user_id" = %(user_id)s) AND (("core_rating"."type"=1 AND "core_rating"."rating" IS NULL) OR "core_rating"."user_id" IS NULL) AND "core_rating"."last_displayed" IS NULL '
        order_by=' ORDER BY "core_film"."popularity" DESC '
        params = {'user_id':str(user_id)}
        
        query = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'params': params
        }

        filters = self.filter_films(query, tags, year_from, year_to, related_director, related_actor, popularity)      
        query, params = self._perform_queries(filters)
        top_films = self.__execute_film_queries(query, params)
        top_films = top_films[:limit]

        return top_films

    def get_recently_popular_films(self, limit=100, user_id=None, rated_films=None):

        top_films = self.get_recently_popular_films_query(user_id, rated_films)

        top_films = top_films[:limit]
        logger.debug("Top movies (sliced): ")
        logger.debug(top_films)
        
        return top_films
        
    def get_best_psi_films_queryset(self, user, tags=None, year_from=None, year_to = None, related_director = None, related_actor = None, popularity = None, include_features=(), exclude_features=(), netflix=None, exclude_production_country=None):
        from film20.recommendations import engine
        is_filtered = tags or year_from or year_to or related_director or related_actor or popularity or netflix
        
        if exclude_production_country:
            kw = dict(exclude_production_country=exclude_production_country)
        else:
            kw = {}
        all_scores = engine.compute_guess_score_for_all_films(user, **kw)
        all_scores = dict((key, val) for key, val in all_scores.items() if val)
        ratings = Rating.get_user_ratings(user)
        shitlisted = set(k for k,v in BasketItem.user_basket(user).items() if v[0]==9)

        film_ids = set(all_scores.keys())
        film_ids.difference_update(ratings.keys())
        film_ids.difference_update(shitlisted)

        if is_filtered:
            filtered = self._filter_films(tags, year_from, year_to, related_director, related_actor, popularity, netflix)
            filtered = filtered.filter(id__in=film_ids)
            film_ids = filtered.values_list('id', flat=True)

        if include_features:
            from film20.film_features.models import FilmFeature
            featured_ids = FilmFeature.matching_film_ids(include_features, exclude_features)
            film_ids = [id for id in film_ids if id in featured_ids]

        film_ids = sorted(film_ids, key=lambda f: -all_scores[f])
        
        from film20.utils.misc import ListWrapper
        class FilmWrapper(ListWrapper):
            def wrap(self, items):
                films = list(Film.objects.filter(id__in=items))
                films.sort(key=lambda f:-all_scores[f.id])
                for film in films:
                    film.guess_rating = all_scores.get(film.id)
                    yield film
        return FilmWrapper(film_ids)

    def _filter_films(self, tags=None, year_from=None, year_to = None, related_director = None, related_actor = None, popularity = None, netflix=None):
        top_films = Film.objects.all()
        if year_from:
            top_films = top_films.filter(release_year__gte = year_from)
        if year_to:
            top_films = top_films.filter(release_year__lte = year_to)
        if related_director:
            for director in related_director:
                top_films = top_films.filter(directors = director.id)
        if related_actor:
            for actor in related_actor:
                top_films = top_films.filter(actors = actor.id, character__LANG = settings.LANGUAGE_CODE)
        if popularity:
            top_films = top_films.filter(popularity__gte = popularity)
        if netflix is not None:
            top_films = top_films.filter(netflix_id__isnull=False)
            if netflix == 'instant':
                top_films = top_films.filter(netflix_instant=True)
        if tags:
            tags = [t.strip() for t in tags.split(',')]
            logger.debug("Enriching query. Filtering by tags: %r", tags)
            for tag in tags:
                top_films = top_films.filter(objectlocalized__tagged_items__tag__name = tag, objectlocalized__LANG = settings.LANGUAGE_CODE)
        return top_films

    def filter_films(self, query, tags=None, year_from=None, year_to=None, related_director=None, related_actor=None, popularity=None):
        # START: handling filtering parameters
        and_word = ' AND '
        select_query = query['select']
        from_query = query['from']
        order_by = query['order_by']
        where = query['where']
        join = query['join']

        params = query['params']
        
        if self.filter_exists(related_director):
            director_id = related_director[0].id
            query_join = ' INNER JOIN "core_film_directors" ON ("core_film"."parent_id" = "core_film_directors"."film_id") '
            join += query_join
            query_director = ' "core_film_directors"."person_id" = %(related_director)s '
            if where:
                where += and_word + query_director
            else:
                where = ' WHERE ' + query_director
            params_director = {'related_director':str(director_id)}
            params.update(params_director)

        if self.filter_exists(related_actor):
            actor_id = related_actor[0].id
            query_join = ' INNER JOIN "core_character" ON ("core_film"."parent_id" = "core_character"."film_id") '
            join += query_join
            query_actor = ' "core_character"."person_id" = %(related_actor)s '
            if where:
                where += and_word + query_actor
            else:
                where = ' WHERE ' + query_actor
            params_actor = {'related_actor':str(actor_id)}
            params.update(params_actor)
       
        if self.filter_exists(year_from):
            query_year_from = ' "core_film"."release_year" >= %(year_from)s '

            if where:
                where += and_word + query_year_from
            else:
                where = ' WHERE ' + query_year_from
            params_year_from = {'year_from':str(year_from)}
            params.update(params_year_from)

        if self.filter_exists(year_to):
            query_year_to = ' "core_film"."release_year" <= %(year_to)s '
            params_year_to = {'year_to':str(year_to)}
            params.update(params_year_to)
            if where:
                where += and_word + query_year_to
            else:
                where = ' WHERE ' + query_year_to

        if popularity is not None:
            query_popularity = ' "core_film"."popularity" >= %(popularity)s '
            params_popularity = {'popularity':str(popularity)}
            params.update(params_popularity)
            if where:
                where += and_word + query_popularity
            else:
                where = ' WHERE ' + query_popularity

        filters = {
            'select': select_query,
            'from': from_query,
            'join': join,
            'where': where,
            'order_by': order_by,
            'params': params
        }

        # TODO: Test filtering with RawQuerySet 
        filters = self.enrich_query_with_tags(filters, tags, "core_film.parent_id")
        # END: handling filtering parameters
        return filters         
    
    # to be removed
    def filter_out_already_rated(self, films, user_id=None):
        """
            Filters out the movies already rated before
            and those currently in user basket
        """    
        # if user_id passed, get all movies rated by the user
        if user_id:
            qset_rated = (
                Q(rating__user__id = user_id) &
                Q(rating__rating__isnull=False)
            )
                        
            rated_films = Film.objects.filter(qset_rated)
            rated_films = rated_films.extra(
                join=['LEFT OUTER JOIN "filmbasket_basketitem" ON ("core_film"."parent_id" = "filmbasket_basketitem"."film_id" and "filmbasket_basketitem"."user_id" = %i' % user_id],
                where=['("filmbasket_basketitem"."wishlist" IS NULL)'],
            )
            rated_films = rated_films.distinct()
            
            logger.debug("Rated movies: ")
            logger.debug(rated_films)
    
            # remove duplicates from the list
            films = list(set(films))
                  
            # remove all rated movies from the list
            for rated_film in list(rated_films):
                try:
                    # this is fine                    
                    films.remove(rated_film)
                    logger.debug("Rated film removed from top list: " + unicode(rated_film))
                except ValueError:
                    # this is fine as well
                    None
    #                logger.debug("Rated film not in top list: " + unicode(rated_film))
        return films
            
    def prepare_films_to_rate(self, user_id, rated_films = None):
        """
            Returns next film to rate for given user, basing on the algorithm
            guessing the movies the user is likely to have seen
        """
    
        logger.debug("User ID = " + unicode(user_id))
        logger.debug("rated_films = " + unicode(rated_films))
        
        limit1 = 20
        limit2 = 1
        top_films = self.get_recently_popular_films(limit=limit1, user_id=user_id)
        shuffle(top_films)

        return top_films                
        
    def get_rating_comparator_for_user(self, curuser, compared_user):
        fetched_comparator = None
        try:
            fetched_comparator = RatingComparator.objects.get(main_user=curuser.id, compared_user=compared_user.id)
        except RatingComparator.DoesNotExist:
            fetched_comparator = None
            
        return fetched_comparator

    def get_nearby_users(self, user, distance, filmaster_type=FILMASTERS_ALL):
        profile = user.get_profile()
        lat, lng = profile.latitude, profile.longitude
        if lat is None or lng is None:
            return ()

        users = User.objects.filter(is_active=True).order_by("distance")

        if filmaster_type == FOLLOWING_ONLY:                
            friends_list = self.get_following_ids_as_list(user)
            users = users.filter(id__in=friends_list)
            
        from geonames import bounds
        n, s, e, w = bounds(float(lat), float(lng), float(distance))
        users = users.filter(profile__latitude__gt=str(s),
                             profile__latitude__lt=str(n),
                             profile__longitude__gt=str(w),
                             profile__longitude__lt=str(e))
        distance = """6371 * 2 * ASIN(SQRT(POWER(SIN((%s - ABS(latitude)) * pi()/180 / 2), 2) + \
                      COS(%s * pi()/180 ) * COS(abs(latitude) * pi()/180) * POWER(SIN((%s-longitude) * pi()/180 / 2), 2)))"""
        params = [lat, lat, lng]
        users = users.extra(select={'distance':distance},
                            select_params=params)
        return users
        
    def get_best_tci_users(self, user=None, min_common_films=15, filmaster_type=FILMASTERS_ALL, sort_by=FILMASTERS_SORT_COMMON_TASTE, limit=-1):
        """
            Gets the top users basing on the taste comparator index
            It gets all the users and then retrieves the score and number of common films 
            for the users for which we have a matching RatingComparator object  
        """
        
        # What we want to achieve here is a query like this:
                
        # select a.username, coalesce(rc.score,999) as score, coalesce(rc.common_films, 0) as common_films 
        # from auth_user a left join core_ratingcomparator rc on a.id=rc.compared_user_id 
        # where rc.main_user_id=3 or rc.main_user_id is null order by score;
        
        top_users = User.objects.filter(is_active=True)
        if not user==None:
            top_users = top_users.order_by("-date_joined")
            dist_cond = False
            
            # TODO: perhaps integrate nicely into the query to always fetch the friendship status
            # so that we can e.g. color friends differently in the gui
            if filmaster_type == FOLLOWING_ONLY:                
                friends_list = self.get_following_ids_as_list(user)
                top_users = top_users.filter(id__in=friends_list)
                
            select=dict(score='COALESCE("core_ratingcomparator"."score",10)', common_films='COALESCE("core_ratingcomparator"."common_films", 0)')
            where=['"core_ratingcomparator"."main_user_id"=%s AND COALESCE("common_films",0)>=%s']
            params=[user.id, min_common_films]

            top_users = top_users.extra(select, where, params)
            top_users.query.join((None,'auth_user', None, None))
            connection=('auth_user', 'core_ratingcomparator', 'id', 'compared_user_id')
            top_users.query.join(connection, promote=True)

            if sort_by == FILMASTERS_SORT_COMMON_FILMS:
                top_users = top_users.order_by("-common_films")
            elif sort_by == FILMASTERS_SORT_NAME:
                top_users = top_users.order_by("username")
            elif sort_by == FILMASTERS_DATE_JOINED:
                top_users = top_users.order_by("-date_joined")
            else:
                # defaults to common taste
                top_users = top_users.order_by("score")

        logger.debug("Top users fetched.")

        top_users = top_users.distinct()

        if limit > 0:
            top_users = top_users[:limit]
        
        return top_users
    
    # helper function to get all friends ids as a list
    def get_following_ids_as_list(self, user):
        """
           returns list with users id that user is following
        """
        return list(f.id for f in user.followers.following())

    # helper function to get all, followed by given user, users ids as a list
    def get_followers_ids_as_list(self, user):
        """
           returns list with users id that given user is followed by
        """
        return list(f.id for f in user.followers.followers())


    def count_ratings(self, user_id):
        """
            Get the number of all ratings by user.
            Cache the result.
        """

        # try to retrieve from cache
        key = cache.Key(cache.CACHE_USER_RATINGS_COUNT, user_id)
        result = cache.get(key)
        if result is not None:
            return result
        
        query = (                                                                
            Q(user=user_id) &
            Q(rating__isnull = False) &
            Q(type=Rating.TYPE_FILM)
        )
        ratings = Rating.objects.filter(query)
        ratings_count = ratings.count()

        # store in cache
        cache.set(key, ratings_count)

        return ratings_count

    # TODO: throw exceptions
    def get_all_ratings(self, user_id, type=Rating.TYPE_FILM, tags = None, year_from = None, year_to = None, related_director = None, related_actor = None, popularity = None, order_by='-rating'):
        """
            Gets all ratings for given user
        """

        query = (
            Q(user=user_id) &
            Q(rating__isnull = False) &
            Q(type=type)
        )

        ratings = Rating.objects.filter(query).select_related('film', 'person')

        if year_from:
            ratings = ratings.filter(film__release_year__gte = year_from)
        if year_to:
            ratings = ratings.filter(film__release_year__lte = year_to)
        if related_director:
            for director in related_director:
                ratings = ratings.filter(film__directors = director.id)
        if related_actor:
            for actor in related_actor:
                ratings = ratings.filter(film__actors = actor.id, film__character__LANG = settings.LANGUAGE_CODE)
        if tags:
            tags = [t.strip() for t in tags.split(',')]
            logger.debug("Enriching query. Filtering by tags: %r", tags)
            for tag in tags:
                ratings = ratings.filter(film__objectlocalized__tagged_items__tag__name = tag, film__objectlocalized__LANG = settings.LANGUAGE_CODE)
        if popularity:
            ratings = ratings.filter(film__popularity__gte = popularity)

        logger.debug("All ratings fetched for user " + unicode(user_id))

        ratings = ratings.order_by(order_by, 'film__title')

        return ratings

    def filter_exists(self, filter_str):
        return bool(filter_str)

    # TODO: remove this method after migrating to django 1.2
    def enrich_query_with_tags(self, objects, tags, film_id_string):
        """
            Add tag filtering to any query (used by ratings, rankings and recommendations so far
             Possibly use for collections as well in the future (there is a task for that)
        """
        if not tags:
            logger.debug("No tags, returning the original object")
            return objects
            
        join_query = objects['join']
        where_query = objects['where']
        params = objects['params']

        if not where_query:
            where_query = ' WHERE '
        else:
            where_query += ' AND '
        order_query = objects['order_by']
        tags = [t.strip() for t in tags.split(',')]
        tags_params = ''
        for t in tags:
            tags_params += t + ', '
        tags_params = tags_params[:-2]

        logger.debug("Enriching query. Filtering by tags: %r", tags)

        join= ' LEFT OUTER JOIN "core_objectlocalized" ON ("core_objectlocalized"."parent_id" = %s) LEFT OUTER JOIN "tagging_taggeditem" ON ("tagging_taggeditem"."object_id" = "core_objectlocalized"."id") LEFT OUTER JOIN "tagging_tag" ON ("tagging_tag"."id" = "tagging_taggeditem"."tag_id") ' % film_id_string
        where=' "tagging_tag"."name" IN (%(tags_params)s) AND "core_objectlocalized"."LANG"=%(language_code)s AND content_type_id=%(content_type)s '
        where_params = {'tags_params': tags_params, 'language_code': LANGUAGE_CODE, 'content_type': ContentType.objects.get_for_model(ObjectLocalized).pk}
        params.update(where_params)

        objects['join'] = join_query + join
        objects['where'] = where_query + where
        objects['params'] = params
        return objects

    def prepare_tags_for_query(self, tags, film_id_string):
        """
            Prepare tag filtering for any query (used by ratings, rankings and recommendations so far,
             possibly use for collections as well in the future).
        """
        if not tags:
            logger.debug("No tags, returning the original object")
            return None

        tags = [t.strip() for t in tags.split(',')]
        tags_params = ', '.join(['%s'] * len(tags))

        logger.debug("Enriching query. Filtering by tags: %r", tags)

        joins = '''
            LEFT OUTER
            JOIN "core_objectlocalized"
            ON ("core_objectlocalized"."parent_id" = core_filmranking.film_id)
            LEFT OUTER
            JOIN "tagging_taggeditem"
            ON ("tagging_taggeditem"."object_id" = "core_objectlocalized"."id")
            LEFT OUTER
            JOIN "tagging_tag"
            ON ("tagging_tag"."id" = "tagging_taggeditem"."tag_id")
        '''

        where = '''
            tagging_tag.name IN (''' + tags_params + ''')
            AND core_objectlocalized."LANG"=%s
            AND content_type_id=%s
        '''

        params = tags + [LANGUAGE_CODE, str(ContentType.objects.get_for_model(ObjectLocalized).pk)]

        result = {
            'joins': joins,
            'where': where,
            'params': params,
        }
        return result

    def get_ranking(self, type=Rating.TYPE_FILM, tags=None, year_from=None, year_to = None, related_director = None,
                    related_actor = None, popularity = None, order_by="average_score", order_way="desc",
                    limit = None, offset = None, min_num_votes = None, festival = False, exclude_production_country=None,
                    include_features=(), exclude_features=(), tv_series=False, **kw):
        """
            Gets film ranking for given type (overall, directory, screenplay, etc)
        """
        if min_num_votes == None:
            # festival hacks
            if festival:
                min_num_votes = 1
            # this is user-entered
            elif popularity is not None:
                min_num_votes = popularity
            elif type == Rating.TYPE_FILM:
                min_num_votes = FilmRanking.MIN_NUM_VOTES_FILM if not tv_series else 0
            else:
                min_num_votes = FilmRanking.MIN_NUM_VOTES_OTHER

        ranking = FilmRanking.objects.filter(type = type, number_of_votes__gte = min_num_votes).select_related('film', 'film__directors', 'film__actors').order_by('-average_score').distinct()
        if tv_series is not None:
            ranking = ranking.filter(film__is_tv_series=tv_series)
        if year_from:
            ranking = ranking.filter(film__release_year__gte = year_from)
        if year_to:
            ranking = ranking.filter(film__release_year__lte = year_to)
        if related_director:
            for director in related_director:
                ranking = ranking.filter(film__directors = director.id)
        if related_actor:
            for actor in related_actor:
                ranking = ranking.filter(film__actors = actor.id, film__character__LANG = settings.LANGUAGE_CODE)
        if tags:
            tags = [t.strip() for t in tags.split(',')]
            logger.debug("Enriching query. Filtering by tags: %r", tags)
            for tag in tags:
                ranking = ranking.filter(film__objectlocalized__tagged_items__tag__name = tag, film__objectlocalized__LANG = settings.LANGUAGE_CODE)

        if exclude_production_country:
            ranking = ranking.exclude(film__production_country_list__icontains=exclude_production_country)

        if include_features:
            from film20.film_features.models import FilmFeature
            featured_ids = FilmFeature.matching_film_ids(include_features, exclude_features)
            ranking = ranking.filter(film__in=featured_ids)

        logger.debug("Ranking fetched for type " + unicode(type))
        return ranking

    def get_films_for_tag(self, tags=None, year_from=None, year_to=None, related_director=None, related_actor=None, popularity=None, order_by="title",limit = None, offset = None):
        """
            Gets a list of films for a tag
        """

        films = Film.objects.all()

        if year_from:
            films = films.filter(release_year__gte = year_from)
        if year_to:
            films = films.filter(release_year__lte = year_to)
        if popularity:
            films = films.filter(popularity__gte = popularity)
        if related_director:
            for director in related_director:
                films = films.filter(directors = director.id)
        if related_actor:
            for actor in related_actor:
                films = films.filter(actors = actor.id, character__LANG = settings.LANGUAGE_CODE)
        if tags:
            tags = [t.strip() for t in tags.split(',')]
            logger.debug("Enriching query. Filtering by tags: %r", tags)
            for tag in tags:
                films = films.filter(objectlocalized__tagged_items__tag__name = tag, objectlocalized__LANG = settings.LANGUAGE_CODE)

        films = films.order_by(order_by)
        films = films[limit:offset]

        logger.debug("Films for tags: %s" % tags)
        return films
    
    def get_last_computed(self, user):
        """
            Gets last computed recommendations for user
        """
        
        query = (                
            Q(user = user.id)
        )
        
        try:
            last_computed = Computed.objects.get(query)
            logger.debug("Last Computed fetched for user " + unicode(user))  
            return last_computed  
        except Computed.DoesNotExist:
            logger.debug("Last Computed not found for user " + unicode(user))    
            return None
        
    def allow_recomputing(self, last_computed):
        if last_computed == None:
            return True
        
        today = datetime.today()
        yesterday = today - timedelta(1)
        
        print "last_computed.updated_at = " + str(last_computed.updated_at)
        print "yesterday = " + str(yesterday)
        
        if last_computed.updated_at > yesterday:
            return False
        else:
            return True
        
    def save_computed(self, user, comparators, recommendations, last_computed=None):
        if last_computed==None:
            logger.debug("Computing recommendations!")
            computed = Computed()
        else:
            logger.debug("Computing recommendations!")
            computed = last_computed
            
        computed.user = user
        computed.comparators = comparators
        computed.recommendations = recommendations
        
        computed.save()
            
