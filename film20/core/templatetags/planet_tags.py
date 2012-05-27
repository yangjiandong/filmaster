from django import template
from film20.blog.models import Post
import film20.settings as settings
from film20.utils.cache_helper import *
from film20.utils import cache_helper as cache
from film20.blog.post_helper import get_related_posts
import logging
logger = logging.getLogger(__name__)

register = template.Library()

NUMBER_OF_REVIEWS_TAG_PAGE = getattr(settings, "NUMBER_OF_REVIEWS_TAG_PAGE", 6)


@register.inclusion_tag('planet/planet_featured_reviews.html')
def show_featured_reviews():

    key = "featured_reviews"

    featured_reviews = get_cache(CACHE_PLANET, key)
    if featured_reviews is None:
        featured_reviews = Post.objects.select_related().filter(
                featured_note=False,
                is_published=True,
                related_film__isnull = False,
                status=Post.PUBLIC_STATUS)
        featured_reviews = featured_reviews.exclude(featured_note=True)
        featured_reviews = featured_reviews.distinct().order_by("-publish")[:NUMBER_OF_REVIEWS_TAG_PAGE]
        set_cache(CACHE_PLANET, key, featured_reviews, CACHE_HALF_HOUR)
        logger.debug("featured_reviews MISS")
    else:
        logger.debug("featured_reviews HIT")

    return { "featured_reviews" : featured_reviews}

@register.inclusion_tag('profile/right_sidebar/related_films.html')
def related_films(post):
    """
        Displays list of films related to the article.
    """

    films = None
    if post.related_film and post.related_film.count > 0:
        films = post.related_film.select_related()

    return {
            'movies': films
    }


@register.inclusion_tag('profile/right_sidebar/related_persons.html')
def related_persons(post):
    """
        Displays list of persons related to the article.
    """

    persons = None
    if post.related_person and post.related_person.count > 0:
        persons = post.related_person.select_related()

    return {
            'persons': persons
    }

@register.inclusion_tag('profile/right_sidebar/related_articles.html')
def related_articles(activity, user):
    """ Displays list of related articles """

    MAX_RELATED_ARTICLES = getattr(settings, 'MAX_RELATED_ARTICLES')

    key = cache.Key("related_posts", activity)
    related_posts = cache.get(key)
    if not related_posts:
        related_posts = get_related_posts(activity, user, MAX_RELATED_ARTICLES)
        cache.set(key, related_posts, cache.A_DAY)

    return {'related_posts': related_posts}


