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
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.conf import settings
import datetime
import random
from film20.utils import cache_helper as cache
LANGUAGE_CODE = settings.LANGUAGE_CODE

from film20.core.models import RatingComparator
from film20.useractivity.models import UserActivity
from film20.blog.models import Post
from film20.recommendations.recom_helper import RecomHelper
from film20.core.models import Object, ShortReview

NUMBER_OF_ACTIVITIES = settings.NUMBER_OF_ACTIVITIES
SIMILAR_USER_LEVEL = 2

def ajax_activity_pager(request, objects, size=settings.NUMBER_OF_ACTIVITIES):
    if 'ajax' in request.GET:
        if request.POST:
            return objects[0:1]
        page_nr = int(request.GET.get('page', 0))
        objects = objects[size * page_nr:size * (page_nr + 1)]
    return objects

def ajax_select_template(request, template_name):
    if 'ajax' in request.GET:
        return 'wall/useractivity/ajax_show_activities.html'
    return template_name

class UserActivityHelper:

    limit = None

    def paginate_activities(self, request, activities):
        paginator = Paginator(activities, NUMBER_OF_ACTIVITIES)
        try:
            page = int(request.GET.get(_('page'), '1'))
        except ValueError:
            raise Http404

        try:
            paginated_activities = paginator.page(page)
        except (EmptyPage, InvalidPage):
            raise Http404
        return paginated_activities

    def main_page_featured_activities(self):
        """Gets list of daily featured activities. """
        #TODO add filtering by featured activities but only when featuring
        #    becomes automatical. http://jira.filmaster.org/browse/FLM-700

        TYPES_OF_ACTIVITIES = \
                getattr(settings, 'MAIN_PAGE_TYPES_OF_ACTIVITIES')

        key = cache.Key('main_page_displayed_activities')
        displayed = cache.get(key)
        if not displayed:
            activities = UserActivity.objects.public().order_by('-created_at')
            displayed = []
            for act_type in TYPES_OF_ACTIVITIES:
                activity_type = vars(UserActivity)[act_type]
                DISPLAYED_NUMBER = TYPES_OF_ACTIVITIES[act_type]
                typed_activities = list(activities.filter(
                        activity_type=activity_type)[:DISPLAYED_NUMBER])
                displayed += typed_activities

            random.shuffle(displayed)
            logger.info(displayed)
            cache.set(key, displayed)

        return displayed

    def get_friends_list(self, request):
        return []

    def get_similar_users_list(self, request):
        users = []
        if request.user.is_authenticated():
            key = cache.Key('similar_users_list', request.user)
            similar_users_list = cache.get(key)
            if not similar_users_list:
                similar_users_list = RatingComparator.objects.filter(main_user=request.user, score__lte=SIMILAR_USER_LEVEL).select_related('user')
                cache.set(key, similar_users_list)
            if similar_users_list:
                for similar_user in similar_users_list:
                    users.append(similar_user.compared_user)
        return users

    def get_followers_list(self, user):
        if not user.is_authenticated(): return []
        followers_list = user.followers.following()
        return followers_list

import logging
logger = logging.getLogger(__name__)
class PlanetHelper(UserActivityHelper):

    def __init__(self, limit=None):
        self.limit = limit

    def get_activities(self, request, all_activities, reviews, most_interesting_reviews, shorts, comments,
                       links, all_users, followed, similar_taste, favorites, follows=False, checkins=False, username=None, exclude_query = None):
        query = Q()
        empty_list = None
        
        activities = UserActivity.objects.public()

        if favorites and request.user.is_authenticated():
            logger.debug("favorites")
            # Removed favorites in http://jira.filmaster.org/browse/FLM-1079
        
        if username:
            logger.debug("username:%s", username)
            activities = activities.filter(username=username)

        if most_interesting_reviews:
            logger.debug("most_interesting_reviews")
            activities = activities.filter(Q(post__featured_note=True) | Q(post__is_published=True))
        else:
            if reviews:
                logger.debug("notes" + str(reviews))
                query = query | Q(activity_type=UserActivity.TYPE_POST)
            if shorts:
                logger.debug("shorts" + str(shorts))
                query = query | Q(activity_type=UserActivity.TYPE_SHORT_REVIEW)
            if comments:
                logger.debug("comments" + str(comments))
                query = query | Q(activity_type=UserActivity.TYPE_COMMENT)
            if links:
                logger.debug("links" + str(links))
                query = query | Q(activity_type=UserActivity.TYPE_LINK)
            if checkins:
                logger.debug("checkins" + str(checkins))
                query = query | Q(activity_type=UserActivity.TYPE_CHECKIN)
            if follows:
                query = query | Q(activity_type=UserActivity.TYPE_FOLLOW)
            
            if query:
                activities = activities.filter(query)

        if not all_users and (followed or similar_taste):
            friend_list = followed and self.get_followers_list(request.user) or ()
            similar_users_list = similar_taste and self.get_similar_users_list(request) or ()
            user_list = set(friend_list) | set(similar_users_list)
            empty_list = not bool(user_list)
            activities = activities.filter(user__in=user_list)

        if exclude_query:
            activities = activities.exclude(exclude_query)

        activities = activities.order_by("-created_at")
        
        print str(activities.query)

        return empty_list, activities
                    
    def planet_followers(self, followers_list):
        followers = UserActivity.objects.select_related('user','post','short_review','comment','link','film').filter(user__in=followers_list, status=UserActivity.PUBLIC_STATUS).order_by("-created_at")

        if self.limit:
            followers = followers[:self.limit]
        
        return followers

    def planet_similar_users(self, users):
        similar_users = UserActivity.objects.select_related('user','post','short_review','comment','link','film').filter(user__in=similar_users_list, object__status=Object.PUBLIC_STATUS).order_by("-created_at")

        if self.limit:
            similar_users = similar_users[:self.limit]
        
        return similar_users

    def planet_short_reviews(self):
        short_reviews = UserActivity.objects.select_related('user','short_review','film',).filter(activity_type=UserActivity.TYPE_SHORT_REVIEW, object__status=Object.PUBLIC_STATUS).order_by("-created_at")
        if self.limit:
            short_reviews = short_reviews[:self.limit]
        return short_reviews

    def planet_notes(self):
        notes = UserActivity.objects.select_related('user','post').filter(activity_type=UserActivity.TYPE_POST, object__status=Object.PUBLIC_STATUS).order_by("-created_at")
        
        if self.limit:
            notes = notes[:self.limit]
        return notes

    def planet_all(self):
        all = UserActivity.objects.select_related('user','post','short_review','comment','link','film').filter(object__status=Object.PUBLIC_STATUS).order_by("-created_at")
        if self.limit:
            all = all[:self.limit]
        return all

    def planet_comments(self):
        comments = UserActivity.objects.select_related('user','comment',).filter(activity_type = UserActivity.TYPE_COMMENT, object__status=Object.PUBLIC_STATUS).order_by("-created_at")
 
        if self.limit:
            comments=comments[:self.limit]
        return comments

    def planet_most_interesting(self):
        notes = UserActivity.objects.select_related('user','post').filter(
                Q(activity_type = UserActivity.TYPE_POST),
                Q(object__status=Object.PUBLIC_STATUS),
                Q(post__featured_note=True)|Q(post__is_published=True)
                ).order_by("-created_at")
        if self.limit:
            notes = notes[:self.limit]
        return notes

    def planet_favourites(self, request):
        favourites = []
        if request.user.is_authenticated():
            favourites = UserActivity.objects.select_related('user','post','short_review','comment','link','film').filter(activity__vote=1, activity__user=request.user, object__status=Object.PUBLIC_STATUS).order_by("-created_at")[:self.limit]
        if self.limit:
            favourites=favourites[:self.limit]
        return favourites
    
    def planet_links(self):
        links = UserActivity.objects.select_related('user','link').filter(activity_type = UserActivity.TYPE_LINK, object__status=Object.PUBLIC_STATUS).order_by("-created_at")

        if self.limit:
            links = links[:self.limit]
        return links
    
class PlanetFilmHelper(UserActivityHelper):

    the_film = None

    def __init__(self, the_film, limit=None):
        self.the_film = the_film
        self.limit = limit

    def planet_film_friends(self, friends_list):
        friends = UserActivity.objects.filter(Q(user__in=friends_list),\
                                            Q(activity_type = UserActivity.TYPE_POST, post__related_film=self.the_film, post__status=Post.PUBLIC_STATUS)|\
                                            Q(activity_type = UserActivity.TYPE_SHORT_REVIEW, film=self.the_film)|\
                                            Q(activity_type = UserActivity.TYPE_COMMENT, film=self.the_film)).order_by("-created_at")[:self.limit]

        return friends

    def planet_film_similar_users(self, similar_users):
        similar_users = UserActivity.objects.filter(Q(user__in=similar_users),\
                                                    Q(activity_type = UserActivity.TYPE_POST,\
                                                      post__related_film=self.the_film,\
                                                      post__status=Post.PUBLIC_STATUS)|\
                                                      Q(activity_type = UserActivity.TYPE_SHORT_REVIEW, film=self.the_film)|\
                                                      Q(activity_type = UserActivity.TYPE_COMMENT, film=self.the_film)).order_by("-created_at")[:self.limit]
        return similar_users

    def planet_film_short_reviews(self):
        short_reviews = UserActivity.objects.filter(activity_type = UserActivity.TYPE_SHORT_REVIEW,\
                                            film=self.the_film).order_by("-created_at")[:self.limit]
        return short_reviews

    def planet_film_notes(self):
        notes = UserActivity.objects.filter(activity_type = UserActivity.TYPE_POST,\
                                            post__related_film=self.the_film,\
                                            post__status=Post.PUBLIC_STATUS)\
                                            .exclude(post__status=Post.DRAFT_STATUS)\
                                            .exclude(post__status=Post.DELETED_STATUS).order_by("-created_at")[:self.limit]
        return notes

    def planet_film_comments(self):
        comments = UserActivity.objects.filter(activity_type = UserActivity.TYPE_COMMENT, film=self.the_film).order_by("-created_at")[:self.limit]
        return comments

    def planet_film_all(self):
        all = UserActivity.objects.filter(Q(activity_type = UserActivity.TYPE_POST,\
                                              post__related_film=self.the_film,\
                                              post__status=Post.PUBLIC_STATUS)|\
                                              Q(activity_type = UserActivity.TYPE_SHORT_REVIEW,film=self.the_film)|\
                                              Q(activity_type = UserActivity.TYPE_LINK,link__film=self.the_film)|\
                                              Q(activity_type = UserActivity.TYPE_COMMENT, film=self.the_film)).order_by("-created_at")[:self.limit]
        return all

    def planet_film_favourites(self, request):
        favouries = []
        if request.user.is_authenticated():
            favourites = UserActivity.objects.filter(Q(activity__vote=1, activity__user=request.user),\
                                              Q(activity_type = UserActivity.TYPE_POST,\
                                                post__related_film=self.the_film,\
                                                post__status=Post.PUBLIC_STATUS)|\
                                              Q(activity_type = UserActivity.TYPE_SHORT_REVIEW,film=self.the_film)|\
                                              Q(activity_type = UserActivity.TYPE_LINK,link__film=self.the_film)|\
                                              Q(activity_type = UserActivity.TYPE_COMMENT, film=self.the_film)).order_by("-created_at")[:self.limit]
        return favourites
    
    def planet_film_links(self):
        links = UserActivity.objects.filter(activity_type = UserActivity.TYPE_LINK, link__film=self.the_film).order_by("-created_at")

        if self.limit:
            links = links[:self.limit]
        return links
    
    
class PlanetPersonHelper(UserActivityHelper):

    person = None

    def __init__(self, person, limit=None):
        self.person = person
        self.limit = limit

    def planet_person_friends(self, friends_list):
        friends = UserActivity.objects.filter(Q(user__in=friends_list),\
                                              Q(activity_type = UserActivity.TYPE_POST, post__related_person=self.person, post__status=Post.PUBLIC_STATUS)|\
                                              Q(activity_type = UserActivity.TYPE_SHORT_REVIEW, person=self.person)|\
                                              Q(activity_type = UserActivity.TYPE_COMMENT, person=self.person)).order_by("-created_at")[:self.limit]

        return friends

    def planet_person_similar_users(self, similar_users):
        similar_users = UserActivity.objects.filter(Q(user__in=users),\
                                                Q(activity_type = UserActivity.TYPE_POST, post__related_person=self.person, post__status=Post.PUBLIC_STATUS)|\
                                                Q(activity_type = UserActivity.TYPE_SHORT_REVIEW, person=self.person)|\
                                                Q(activity_type = UserActivity.TYPE_COMMENT, person=self.person)).order_by("-created_at")[:self.limit]
        return similar_users

    def planet_person_short_reviews(self):
        short_reviews = UserActivity.objects.filter(activity_type = UserActivity.TYPE_SHORT_REVIEW, person=self.person).order_by("-created_at")[:self.limit]
        return short_reviews
    def planet_person_notes(self):
        notes = UserActivity.objects.filter(activity_type = UserActivity.TYPE_POST, post__related_person=self.person, post__status=Post.PUBLIC_STATUS).order_by("-created_at")[:self.limit]
        return notes

    def planet_person_all(self):
        all = UserActivity.objects.filter(Q(activity_type = UserActivity.TYPE_POST, post__related_person=self.person, post__status=Post.PUBLIC_STATUS)|\
                                            Q(activity_type = UserActivity.TYPE_SHORT_REVIEW, person=self.person)|\
                                            Q(activity_type = UserActivity.TYPE_COMMENT, person=self.person)).order_by("-created_at")[:self.limit]
        return all

    def planet_person_comments(self):
        comments = UserActivity.objects.filter(activity_type = UserActivity.TYPE_COMMENT, person=self.person).order_by("-created_at")[:self.limit]
        return comments

    def planet_person_favourites(self, request):
        favourites = []
        if request.user.is_authenticated():
            favourites = UserActivity.objects.filter(Q(activity__vote=1, activity__user=request.user),\
                                          Q(activity_type = UserActivity.TYPE_POST, post__related_person=self.person, post__status=Post.PUBLIC_STATUS)|\
                                          Q(activity_type = UserActivity.TYPE_SHORT_REVIEW, person=self.person)|\
                                          Q(activity_type = UserActivity.TYPE_COMMENT, person=self.person)).order_by("-created_at")[:self.limit]
        return favourites

class PlanetTagHelper(UserActivityHelper):

    tag = None
    recom_helper = None

    def __init__(self, limit=None, tag=None):
        self.limit = limit
        self.tag = tag
        self.recom_helper = RecomHelper()

    def __perform_queries(self, query_with_tags):
        select_query = query_with_tags['select'] if query_with_tags['select'] is not None else ''
        from_query = query_with_tags['from'] if query_with_tags['from'] is not None else ''
        join_query = query_with_tags['join'] if query_with_tags['join'] is not None else ''
        where_query = query_with_tags['where'] if query_with_tags['where'] is not None else ''
        order_by = query_with_tags['order_by'] if query_with_tags['order_by'] is not None else ''

        query = select_query + from_query + join_query + where_query + order_by
        params = query_with_tags['params']
        return query, params

    def __execute_queries(self, query, params):
        activities = UserActivity.objects.raw(query, params)
        query = list(activities)[:self.limit]
        return query

    def planet_tag_friends(self, friends_list):
        
        if len(friends_list) == 0:
            friends_list = [0]
        
        select_query = 'SELECT DISTINCT "useractivity_useractivity".* '
        from_query = ' FROM "useractivity_useractivity" '
        join_query = ''' LEFT OUTER JOIN "blog_post" ON ("useractivity_useractivity"."post_id" = "blog_post"."parent_id")
         LEFT OUTER JOIN "core_object" ON ("blog_post"."parent_id" = "core_object"."id") '''
        where_query = ' WHERE ("useractivity_useractivity"."LANG" = %(lang)s AND '
        where_query += ' "useractivity_useractivity"."user_id" IN (%s) ' %str(friends_list)[1:-1]
        where_query += ' AND (("core_object"."status" = %(public_status)s  AND "useractivity_useractivity"."activity_type" = %(type_post)s ) OR "useractivity_useractivity"."activity_type" = %(type_short_review)s  OR "useractivity_useractivity"."activity_type" = %(type_comment)s ))'
        order_by = ' ORDER BY created_at DESC'
        params = {'lang':str(LANGUAGE_CODE), 'public_status': str(Post.PUBLIC_STATUS), 'type_post': str(UserActivity.TYPE_POST), 'type_short_review': str(UserActivity.TYPE_SHORT_REVIEW), 'type_comment': str(UserActivity.TYPE_COMMENT)}

        query_planet_tag_friends = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'limit_and_offset': None,
            'params': params
        }
        query_with_tags = self.recom_helper.enrich_query_with_tags(query_planet_tag_friends, self.tag, film_id_string="useractivity_useractivity.film_id")
        query, params = self.__perform_queries(query_with_tags)
        activities = self.__execute_queries(query, params)
        return activities

    def planet_tag_similar_users(self, similar_users):
        
        similar_users_list = []
        for user in similar_users:
            similar_users_list.append(user.id)
        
        if len(similar_users_list) == 0:
            similar_users_list = [0]
        
        select_query = 'SELECT DISTINCT "useractivity_useractivity".* '
        from_query = ' FROM "useractivity_useractivity" '
        join_query = ''' LEFT OUTER JOIN "blog_post" ON ("useractivity_useractivity"."post_id" = "blog_post"."parent_id")
         LEFT OUTER JOIN "core_object" ON ("blog_post"."parent_id" = "core_object"."id") '''
        where_query = ' WHERE ("useractivity_useractivity"."LANG" = %(lang)s '
        where_query += ' AND "useractivity_useractivity"."user_id" IN ( %s ) ' % str(similar_users_list)[1:-1]
        where_query += ' AND (("core_object"."status" = %(public_status)s  AND "useractivity_useractivity"."activity_type" = %(type_post)s ) OR "useractivity_useractivity"."activity_type" = %(type_short_review)s  OR "useractivity_useractivity"."activity_type" = %(type_comment)s )) '
        order_by = ' ORDER BY "useractivity_useractivity"."created_at" DESC'
        params = {'lang': str(LANGUAGE_CODE), 'public_status': str(Post.PUBLIC_STATUS), 'type_post': str(UserActivity.TYPE_POST), 'type_short_review': str(UserActivity.TYPE_SHORT_REVIEW), 'type_comment': str(UserActivity.TYPE_COMMENT)}

        query_planet_tag_similar_users = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'limit_and_offset': None,
            'params': params
        }

        query_with_tags = self.recom_helper.enrich_query_with_tags(query_planet_tag_similar_users, self.tag, film_id_string="useractivity_useractivity.film_id")
        query, params = self.__perform_queries(query_planet_tag_similar_users)
        activities = self.__execute_queries(query, params)
        return activities

    def planet_tag_reviews(self):
        select_query = 'SELECT "useractivity_useractivity".* '
        from_query = ' FROM "useractivity_useractivity" '
        join_query = ''
        where_query = ' WHERE ("useractivity_useractivity"."LANG" = %(lang)s AND "useractivity_useractivity"."activity_type" = %(activity_type)s) '
        order_by = ' ORDER BY "created_at" DESC'
        params = {'lang':str(LANGUAGE_CODE), 'activity_type':str(UserActivity.TYPE_SHORT_REVIEW)}

        query_planet_tag_reviews = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'limit_and_offset': None,
            'params': params
        }

        query_with_tags = self.recom_helper.enrich_query_with_tags(query_planet_tag_reviews, self.tag, film_id_string="useractivity_useractivity.film_id")
        query, params = self.__perform_queries(query_with_tags)
        activities = self.__execute_queries(query, params)
        return activities

    def planet_tag_notes(self):
        select_query = 'SELECT DISTINCT "useractivity_useractivity".* '
        from_query = ' FROM "useractivity_useractivity" '
        join_query = ''' LEFT OUTER JOIN "blog_post" ON ("useractivity_useractivity"."post_id" = "blog_post"."parent_id")
             LEFT OUTER JOIN "core_object" ON ("blog_post"."parent_id" = "core_object"."id")
             INNER JOIN "blog_post_related_film" ON ("blog_post"."parent_id" = "blog_post_related_film"."post_id")
             INNER JOIN "core_film" ON ("blog_post_related_film"."film_id" = "core_film"."parent_id")
             INNER JOIN "core_object" T6 ON ("core_film"."parent_id" = T6."id") '''
        where_query = ' WHERE ("useractivity_useractivity"."LANG" = %(lang)s AND "core_object"."status" = 1  AND T6."status" = 1  AND "useractivity_useractivity"."activity_type" = 1  AND NOT (("core_object"."status" = 2  AND NOT ("blog_post"."parent_id" IS NULL))) AND NOT (("core_object"."status" = 3  AND NOT ("blog_post"."parent_id" IS NULL)))) '
        order_by = ' ORDER BY "created_at" DESC'
        params = {'lang':str(settings.LANGUAGE_CODE), 'draft_status':str(Post.DRAFT_STATUS), 'deleted_status':str(Post.DELETED_STATUS), 'activity_type': str(UserActivity.TYPE_SHORT_REVIEW)}

        query_planet_tag_notes = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'limit_and_offset': None,
            'params': params
        }

        query_with_tags = self.recom_helper.enrich_query_with_tags(query_planet_tag_notes, self.tag, film_id_string="blog_post_related_film.film_id" )
        query, params = self.__perform_queries(query_with_tags)
        activities = self.__execute_queries(query, params)
        return activities

    def planet_tag_comments(self):
        select_query = 'SELECT "useractivity_useractivity".* '
        from_query = ' FROM "useractivity_useractivity" '
        join_query = ''
        where_query = ' WHERE ("useractivity_useractivity"."LANG" = %(lang)s  AND "useractivity_useractivity"."activity_type" = %(activity_type)s) '
        order_by = ' ORDER BY "created_at" DESC'
        params = {'lang':str(LANGUAGE_CODE), 'activity_type':str(UserActivity.TYPE_COMMENT)}

        query_planet_tag_comments = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'limit_and_offset': None,
            'params': params
        }

        query_with_tags = self.recom_helper.enrich_query_with_tags(query_planet_tag_comments, self.tag, film_id_string="useractivity_useractivity.film_id" )
        query, params = self.__perform_queries(query_with_tags)
        activities = self.__execute_queries(query, params)
        return activities

    def planet_tag_all(self):
        select_query = 'SELECT DISTINCT "useractivity_useractivity".* '
        from_query = ' FROM "useractivity_useractivity" '
        join_query = ''' LEFT OUTER JOIN "blog_post" ON ("useractivity_useractivity"."post_id" = "blog_post"."parent_id")
         LEFT OUTER JOIN "core_object" ON ("blog_post"."parent_id" = "core_object"."id")
         LEFT OUTER JOIN "blog_post_related_film" ON ("blog_post"."parent_id" = "blog_post_related_film"."post_id")
         LEFT OUTER JOIN "core_film" ON ("blog_post_related_film"."film_id" = "core_film"."parent_id")
         LEFT OUTER JOIN "core_object" T6 ON ("core_film"."parent_id" = T6."id") '''
        where_query = ' WHERE ("useractivity_useractivity"."LANG" = %(lang)s  AND (("core_object"."status" = 1  AND T6."status" = 1  AND "useractivity_useractivity"."activity_type" = 1 ) OR "useractivity_useractivity"."activity_type" = 2  OR "useractivity_useractivity"."activity_type" = 3 )) '
        order_by = ' ORDER BY "created_at" DESC'
        params = {'lang':str(LANGUAGE_CODE)}

        query_planet_tag_all = {
            'select': select_query,
            'from': from_query,
            'join': join_query,
            'where': where_query,
            'order_by': order_by,
            'limit_and_offset': None,
            'params': params
        }

        query_with_tags = self.recom_helper.enrich_query_with_tags(query_planet_tag_all, self.tag, film_id_string="useractivity_useractivity.film_id" )
        query, params = self.__perform_queries(query_with_tags)
        activities = self.__execute_queries(query, params)
        return activities

    def planet_tag_favourites(self, request):
        # Removed in http://jira.filmaster.org/browse/FLM-1079
        return None
