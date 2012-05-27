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
from django.db.models import Q

from film20.tagging.forms import TagField

from django.contrib.auth.models import User
from film20.core.models import Object
from film20.core.models import ObjectLocalized
from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Character
from film20.core.models import Rating
from film20.core.models import RatingComparator
from film20.core.models import ShortReview
from film20.core.models import FilmRanking
from film20.recommendations.recom_helper import RecomHelper
from film20.core.object_helper import *
from film20.core.film_forms import *
from film20.tagging.models import TaggedItem, Tag
from film20.core.models import FilmComparator
import film20.settings as settings
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE
from film20.utils.cache_helper import *

import logging
logger = logging.getLogger(__name__)

# constants
NUMBER_OF_COMMENTS_FRONT_PAGE = getattr(settings, "NUMBER_OF_COMMENTS_FRONT_PAGE", 5)
NUMBER_OF_RECOMMENDED_FILMS_FRONT_PAGE = getattr(settings, "NUMBER_OF_RECOMMENDED_FILMS_FRONT_PAGE", 3)
NUMBER_OF_ITEMS_PUBLIC_PROFILE = getattr(settings, "NUMBER_OF_ITEMS_PUBLIC_PROFILE", 5)
SIMILAR_FILMS_ALGORITHM = getattr(settings, "SIMILAR_FILMS_ALGORITHM", "alg2")

class FilmHelper(ObjectHelper):
    """
    A ``Helper`` object for films, to faciliate common static operations
    """
    
    def _same_director_q(self, film):
        return Film.objects.filter(directors__in=film.directors.all()).exclude(id=film.id).distinct()
    
    def get_related_localized_objects(self, film, count):
        # try to retrieve from cache
        result = get_cache(CACHE_RELATED_FILMS, film.id)
        if result is not None:
            return result

        # nothing in cache, retrieve from database
        localized_obj = ObjectLocalized.objects.filter(parent=film.id, LANG__in=['en', 'pl',])
        if localized_obj == None:
            logger.debug("no localized obj for film %s" % film)
            return []
        elif len(localized_obj)==0:
            logger.debug("localized obj for film %s returned but includes 0 elements" % film)
            return []
        
        if SIMILAR_FILMS_ALGORITHM == "alg2":
            compared_films = FilmComparator.objects.values_list('compared_film', flat=True)\
                                        .filter(main_film=film)\
                                        .exclude(compared_film=film).order_by("-score")[:count]
            films_list = list(compared_films)
            related = ObjectLocalized.objects.filter(parent__id__in=films_list, LANG=localized_obj[0].LANG)
        elif SIMILAR_FILMS_ALGORITHM == "alg1":
            directors_q = ObjectLocalized.objects.filter(parent__in=self._same_director_q(film), LANG=localized_obj[0].LANG)
            related = TaggedItem.objects.get_related(localized_obj[0], directors_q, count)
            for o in related:
                o.similarity += Tag.objects.get_base_weight()
            films_q = ObjectLocalized.objects.filter(parent__in=Film.objects.values('pk').query)
            qw = Film.objects.values('pk').query
            logger.debug(qw)
            related_by_tags1 = TaggedItem.objects.get_related(localized_obj[0], films_q, count)
            for o in related_by_tags1:
                if not o in related:
                    related.append(o)
#           if localized_obj[1] != None:
            if len(localized_obj)>1:
                related_by_tags2 = TaggedItem.objects.get_related(localized_obj[1], films_q, count)
                for o in related_by_tags2:
                    if not o in related:
                        related.append(o)

            related.sort(lambda x,y: int(y.similarity-x.similarity or y.parent.film.popularity-x.parent.film.popularity))

        result = related[:count]
        # store in cache
        set_cache(CACHE_RELATED_FILMS, film.id, result)
        return result
       
    
    def get_best_films(self, tags=None, year_from=None, year_to = None,
            related_director = None, related_actor = None, popularity = None,
            number_of_films=None):
        """
            Fetch movies from best to worst
        """
        query = (
            Q(filmranking__type = Rating.TYPE_FILM) &
            Q(filmranking__number_of_votes__gte = FilmRanking.MIN_NUM_VOTES_FILM)
        )

        key = Key(tags, year_from, year_to, related_director, related_actor, popularity, number_of_films)
        best_films = get(key)

        if not best_films:
            best_films = Film.objects.filter(query)

            if year_from:
                best_films = best_films.filter(release_year__gte = year_from)
            if year_to:
                best_films = best_films.filter(release_year__lte = year_to)
            if related_director:
                for director in related_director:
                    best_films = best_films.filter(directors = director.id)
            if related_actor:
                for actor in related_actor:
                    best_films = best_films.filter(actors = actor.id,
                            character__LANG = LANGUAGE_CODE)
            if tags:
                tags = [t.strip() for t in tags.split(',')]
                for tag in tags:
                    best_films = best_films.filter(
                            objectlocalized__tagged_items__tag__name = tag,
                            objectlocalized__LANG = LANGUAGE_CODE
                    )

            best_films = best_films.order_by("-filmranking__average_score")
            if number_of_films:
                return best_films[:number_of_films]

            set(key, best_films)
        return best_films

    NUMBER_OF_USER_BEST_FILMS = getattr(settings, 'NUMBER_OF_USER_BEST_FILMS')

    def get_users_best_films(self, user,
            number_of_films=NUMBER_OF_USER_BEST_FILMS):
        """ Fetch user's best rated films"""

        query = (
            Q(rating__user = user) &
            Q(rating__type = Rating.TYPE_FILM) &
            Q(rating__rating__isnull = False)
        )

        best_films = Film.objects.filter(query).order_by(
                "-rating__rating")[:number_of_films]

        return list(best_films)

    def get_popular_films(self, number_of_films=10, exclude_nonEnglish=False):
        """
        Returns films with most votes. Excludes non-english titles
        for the english version.
        """

        query = (
            Q(filmranking__type = Rating.TYPE_FILM) &
            Q(filmranking__number_of_votes__gte = FilmRanking.MIN_NUM_VOTES_FILM)
        )

        if exclude_nonEnglish:
            query = query & (
                    Q(filmranking__film__production_country_list__contains = 'USA') |
                    Q(filmranking__film__production_country_list__contains = 'UK'))

        popular_films = Film.objects.filter(query).order_by(
                "-filmranking__number_of_votes")[:number_of_films]

        return popular_films

    def get_others_ratings(self, object_id, user_id):
        """
        Returns a list of ratings for the given film, by the users who
        have the most common movie taste to the given user.
        
        If no user_id specified, just return most recent users' ratings. 
        """

        # try to retrieve from cache
        result = get_cache(CACHE_OTHERS_RATINGS, str(object_id) + "_v2_" + str(user_id))
        if result!=None:
            return result

        ratings = None
        userratings = []
        
        logger.debug("Getting others ratings...")
                              
        qset = (
            Q(parent__id = object_id) &
            Q(type = Rating.TYPE_FILM) &
            Q(rating__isnull = False)
        )
                 
        ratings = Rating.objects.filter(qset)
        ratings = ratings.extra(
            select={
                    'score': 'core_ratingcomparator.score',
            },
            tables = ['core_ratingcomparator'],
            where = [
                'core_ratingcomparator.main_user_id = core_rating.user_id',
                'core_ratingcomparator.compared_user_id = %i' % user_id,
            ]                                
        )
        ratings = ratings.select_related('user')
        # TODO: there was a strange error here, commented out to finally fix it now
        ratings = ratings.order_by("score")[:settings.NUMBER_OF_OTHERS_RATINGS]
        # store in cache
        set_cache(CACHE_OTHERS_RATINGS, str(object_id) + "_v2_" + str(user_id), ratings)

        return ratings
    
    def get_recent_ratings_for_film(self, object_id,  ALL=False):
        """
        Returns a list of ratings for the given film, sorted by date
        """
        ratings = None
        userratings = []
        
        logger.debug("Getting recent others ratings...")
                              
        qset = (
            Q(parent__id = object_id) &
            Q(type = Rating.TYPE_FILM) &
            Q(rating__isnull = False)
        )
                 
        ratings = Rating.objects.filter(qset)
        if not ALL:
            ratings = ratings.order_by("-last_rated")[:settings.NUMBER_OF_OTHERS_RATINGS]

        return ratings
    
    def get_film(self, permalink):

        # try to retrieve from cache
        result = get_cache(CACHE_FILM, permalink)
        if result!=None:
            return result
        
        film = Film.objects.select_related().get(parent__permalink=permalink) 
        
        # store in cache
        set_cache(CACHE_FILM, permalink, film)

        return film
    
    def get_film_directors(self, the_film):
        # try to retrieve from cache
        result = get_cache(CACHE_FILM_DIRECTORS, the_film.permalink)
        if result!=None:
            return result

        qset_directors = (
            Q(films_directed = the_film)
        )
        directors = Person.objects.filter(qset_directors)
        
        # store in cache
        set_cache(CACHE_FILM_DIRECTORS, the_film.permalink, directors)

        return directors
    
    def get_film_actors(self, the_film, offset=0, limit=10, LANG=LANGUAGE_CODE):
        # try to retrieve from cache
        cache_path = the_film.permalink + "_" + str(offset) + "_" + str(limit)
        result = get_cache(CACHE_FILM_ACTORS, cache_path)
        if result!=None:
            return result

        qset_actors = (
            Q(film=the_film) &
            Q(person__isnull = False) &
            Q(person__parent__permalink__isnull = False) &
            Q(LANG=LANG)
        )
        actors = the_film.get_actors(LANG)[offset:limit]

        # store in cache
        set_cache(CACHE_FILM_ACTORS, cache_path, list(actors))

        return actors
    
    def get_favorite_films(self, user):
        """ 
        Fetch user's favorite films
        """        
        
        # TODO: optimize -- a query is executed for each film now!!
        qset = (
            Q(user=user) &
            Q(type=Rating.TYPE_FILM) &
	    Q(rating__isnull = False) &
            Q(film__permalink__isnull = False)
        )
        favorite_films = Rating.objects.select_related("film").filter(qset).order_by('-rating')[:NUMBER_OF_ITEMS_PUBLIC_PROFILE]
        return favorite_films
            
    def get_film_localized_title_form(self, the_film, POST=None):
        if POST==None:
            return FilmLocalizedTitleForm(
                initial = {
                    'localized_title': the_film.get_localized_title(),
                }
            )
        else:
            return FilmLocalizedTitleForm(POST)
        
    def handle_edit_localized_title(self, the_film, the_form):
        """
        Handles the localized title editing form.
        """
        is_valid = the_form.is_valid()
        
        if is_valid:       
            localized_title = the_form.cleaned_data['localized_title']
            the_film.save_localized_title(localized_title)
            logger.debug("Localized title saved: " + localized_title)
            
        return is_valid
    
    def get_film_description_form(self, the_film, POST=None):
        if POST==None:
            return FilmDescriptionForm(
                initial = {
                    'description': the_film.get_description(),
                }
            )
        else:
            return FilmDescriptionForm(POST)
        
    def handle_edit_description(self, the_film, the_form):
        """
        Handles the description editing form.
        """
        is_valid = the_form.is_valid()
        
        if is_valid:       
            description = the_form.cleaned_data['description']
            the_film.save_description(description)
            logger.debug("Description saved: " + description)
            
        return is_valid
    
    def handle_edit_short_review(self, user, the_form, object):
        """
        Handles the short_review editing form.
        """
        logger.debug("Editing short review")
        is_valid = the_form.is_valid()
        
        if is_valid:       
            logger.debug("Editing short review - form valid!")
            review_text = the_form.cleaned_data['review_text']
            object_id = the_form.cleaned_data['object_id']
            edit_id = the_form.cleaned_data['edit_id']
            
            # if object is not passed, get object from DB
            if object==None:
                try: 
                    object = Object.objects.get(id=object_id)
                except Object.DoesNotExist:     
                    logger.error("Object of id = %s does not exists. Error!" % object_id)
                    return False       

            # delete
            if the_form.is_empty():
                # delete the short review
                try:
                    # edit existing short review
                    sr = self.get_short_review(
                        object = object,
                        user = user
                    )
                    logger.debug("ShortReview exists, deleting...")
                    sr.delete()
                    logger.debug("Short review deleted!")
                except ShortReview.DoesNotExist:
                    logger.error("Trying to delete a short review that does not exist!")
                    return False
            # edit / add
            else:
# TODO: REMOVE CODE BELOW
#                try:
#                    # edit existing short review
#                    logger.info((object, type(object), user, type(user)))
#                    sr = self.get_short_review(
#                        object = object,
#                        user = user
#                    )
#                    logger.debug("ShortReview exists, editing...")
#                    sr.review_text = review_text
#                    sr.save()
#                except ShortReview.DoesNotExist:
#                    # add new short review
#                    logger.debug("ShortReview does not exist, adding...")

                sr = ShortReview(
                    type = ShortReview.TYPE_SHORT_REVIEW,
                    permalink = 'FIXME',
                    status = 1,
                    version = 1,
                    kind = ShortReview.REVIEW,
                    object=object,
                    user=user,
                    review_text = review_text,
                )
                sr.save()
                
            logger.debug("Short review saved: " + review_text)
        else:
            logger.debug("Editing short review - form invalid!")
            
        return is_valid and sr
    
    def get_short_review_form(self, object, user=None, the_form=None):
        
        if the_form==None:            
            logger.debug("Getting short review [no form]...")
            if ( ( user==None ) | ( user.is_authenticated()==False )):
                logger.debug("User is None, so returning default form...")
                return ShortReviewForm()
            else:
                return ShortReviewForm(
                    initial = {
                         'object_id': object.id,
                    }
                )


#            try:
#                short_review = self.get_short_review(
#                    object = object,
#                    user = user
#                )
#                logger.debug("Preparing new ShortReviewForm")
#                return ShortReviewForm(
#                    initial = {
#                        'edit_id': short_review.id,
#                        'object_id': object.id,
#                        'review_text': short_review.review_text,
#                    }
#                )
#            except ShortReview.DoesNotExist:
#                logger.debug("No short review in DB for user/object, so returning default form...")
#                return ShortReviewForm(
#                    initial = {
#                         'object_id': object.id,
#                    }
#                )
                
        else:
            logger.debug("Getting short review [from form]...")
            return ShortReviewForm(the_form)
    
    # throws ShortReview.DoesNotExist
    def get_short_review(self, object, user):
        """
            Get short review for the current user, object and language code
        """

        # Check if short review exists for this object
        sr = ShortReview.objects.get(
            object=object,
            user=user,
            LANG=LANGUAGE_CODE,
        )           
        return sr       
        
    def get_related_posts(self, permalink):
        """
            Get blog posts related with the film
        """
        from film20.blog.models import Post 
        related_posts = Post.objects.select_related()
        related_posts = related_posts.filter(related_film__permalink = permalink)
        related_posts = related_posts.filter(status = Post.PUBLIC_STATUS)
        
        related_posts = related_posts.extra(
            select={
                    'related_film_count': 'select count(*) from blog_post_related_film where post_id=blog_post.parent_id'
            },
        )
        
        related_posts = related_posts.order_by("related_film_count", "-blog_post.publish")

        related_posts = related_posts[:2]
        
        return related_posts
    
    def get_external_links(self, permalink):
        from film20.externallink.externallink_helper import get_links_for_movie
        return get_links_for_movie(permalink)

    def get_external_videos(self, permalink):
        from film20.externallink.externallink_helper import get_videos_for_movie
        return get_videos_for_movie(permalink)
        
    def get_external_links_form(self):
        from film20.externallink.forms import ExternalLinkForm
        form = ExternalLinkForm()
        return form
    
    def get_external_video_form(self):
        from film20.externallink.forms import ExternalVideoForm
        external_video_form = ExternalVideoForm()
        return external_video_form
        
