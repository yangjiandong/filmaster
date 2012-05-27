from django import template
from film20.config import *
from film20.utils import cache_helper as cache
import film20.settings as settings
from film20.utils.avatars import get_avatar_path
from film20.core.templatetags import display_user
import logging
from django.contrib.contenttypes.models import ContentType
from film20.core.urlresolvers import reverse

SUBDOMAIN_AUTHORS = getattr(settings, "SUBDOMAIN_AUTHORS", False)
SUBDOMAIN_AUTHORS = getattr(settings, "SUBDOMAIN_AUTHORS", False)
DOMAIN = getattr(settings, "DOMAIN", '')
FULL_DOMAIN = getattr(settings, "FULL_DOMAIN", '')
MAX_USERNAME_LENGTH_DISPLAY = getattr(settings, "MAX_USERNAME_LENGTH_DISPLAY", 12)

register = template.Library()

@register.simple_tag
def url_note(activity):
    """
        Returns url for note activity,
        if there are spoilers show spoiler warning
    """
    the_url = ""
    if activity.spoilers:
        the_url += "<img src=\"/static/img/spoiler.png\" alt=\"Spoiler!\" /> "

    get_absolute_url = activity.get_absolute_url() if activity.get_absolute_url() is not None else ''
    get_title = activity.get_title() if activity.get_title() is not None else ''
    the_url += "<a href=\""+ get_absolute_url +"\">"
    the_url += get_title
    the_url += "</a>"

    return the_url

@register.simple_tag
def permalink_film(activity):
    """
        Returns url for film related with activity
    """
    if activity.film_permalink is not None:
        the_permalink = FULL_DOMAIN+"/"+ urls.urls['FILM'] +"/" + activity.film_permalink +"/"
        return the_permalink
    else:
        return ""

@register.simple_tag
def comment_form_url(activity, app_label, model):
    """
        Returns url planet comment form
    """

    key = cache.Key("planet-comment-form", app_label, model)
    content_type = cache.get(key)

    if content_type is None:
        content_type = ContentType.objects.get(app_label=app_label, model=model).id
        cache.set(key, content_type)

    kwargs = {
        'content_type' : content_type,
        'object_id' : activity.object_id,
    }

    return reverse('tc_comment', kwargs=kwargs)

@register.simple_tag
def avatars(size, activity_username):
    """
        Returns url to user avatar
    """

    return get_avatar_path(activity_username, size)

@register.inclusion_tag('user/common_taste_indicator.html')
def compare_users(user, activity_username):
    """
        Compares users taste
    """
    if user.username != activity_username:
        return display_user.compare_users(user, activity_username, is_username=True)
    else:
        return ""

@register.inclusion_tag('profile/article/article_title.html')
def article_title(activity):
    return {
        "activity" : activity,
    }

@register.inclusion_tag('profile/wall_post/wall_post_title.html')
def wall_post_title(activity):
    return {
        "activity" : activity,
    }

@register.inclusion_tag('profile/activity_subscribe_form.html', takes_context=True)
def activity_subscribe_form(context, activity):
    from film20.useractivity.forms import SubscribeForm
    request = context['request']
    if request.user and request.user.is_authenticated():
        form = SubscribeForm(activity=activity, user=request.user)
    else:
        form = None
    return {
        "activity": activity,
        "form": form,
    }

@register.inclusion_tag('wall/useractivity/remove_link.html', takes_context=True )
def remove_link( context, activity ):
    return {
        'activity': activity,
        'can_remove': activity.can_remove( context['request'].user )
    }
