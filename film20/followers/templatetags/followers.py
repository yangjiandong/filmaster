from django import template
from django.template import RequestContext
from film20.core.models import RatingComparator
from django.core.context_processors import request
from film20.core.templatetags.map_url import url_username_link
import film20.settings as settings

register = template.Library()
SUGGESTED_USERS = getattr(settings, "SUGGESTED_USERS", "michuk, ayya, queerdelys, Esme")
FOLLOWED_USERS_FOR_WIDGET = getattr(settings, "FOLLOWED_USERS_FOR_WIDGET", 9)

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.templatetags.map_url import url_user_link

@register.inclusion_tag('filmasters/follow_widget.html')
def follow_widget(next, user, comment_user):
    """
       next = url where user will be redirecter after sucessfull adding to list
       user = logged in user
       comment_user = user want to follow/block him
    """
    if next == "PROFILE":
        next = url_user_link(comment_user)
        
    if user != comment_user:
        relation = user.followers.get_relation(comment_user)
        return {
            "you" : False,
            "relation" : relation,
            "user" : user,
            "comment_user" : comment_user,
            "next" : next,
        }
    else:
        return {
            "you" : True
        }

def follow(user, followers):
    """
        Returns following list for user
        "users that I follow"
    """

    follow = []
    number = []
    if "following" in followers:
        follow = user.followers.following()
        number = follow.count()
    if "followers" in followers:
        follow = user.followers.followers()
        number = follow.count()

    return {
        'follow' : follow[:FOLLOWED_USERS_FOR_WIDGET],
        'number': number,
        'user_profile' : user,
    }

@register.inclusion_tag('aside/dashboard/following.html')
def dashboard_following(user):
    """
        Returns following list for user
        "users that I follow"
    """
    return follow(user, "following")

@register.inclusion_tag('aside/dashboard/followers.html')
def dashboard_followers(user):
    """
        Returns following list for user
        "users that follow me"
    """
    return follow(user, "followers")

@register.inclusion_tag('aside/profile/following.html')
def profile_following(user):
    """
        Returns following list for user
        "users that he/she follows"
    """
    return follow(user, "following")

@register.inclusion_tag('aside/profile/followers.html')
def profile_followers(user):
    """
        Returns following list for user
        "users that follow her/him"
    """
    return follow(user, "followers")

@register.inclusion_tag('followers/recommended_users.html',takes_context=True)
def follow_recommended(context):
    """
        Returns recommended users with follow button
    """

    recommended_users = User.objects.filter(username__in = SUGGESTED_USERS)

    return {
        'users' : recommended_users,
        'request':context['request']
    }

@register.inclusion_tag('followers/recommended_users2.html',takes_context=True)
def follow_similar_taste(context, user):
    """
        Returns recommended users with similar taste
    """
    SIMILAR_USER_LEVEL = 2

    similar_users_list = RatingComparator.objects.filter(main_user=user, score__lte=SIMILAR_USER_LEVEL)[:6]
    users = []
    if similar_users_list:
        for similar_user in similar_users_list:
            users.append(similar_user.compared_user)

    return {
        'users' : users,
        'request':context['request']
    }

@register.simple_tag
def follow_html(text):
    from film20.followers.models import FOLLOW_TXT
    username1, txt, username2 = text.split(' ')

    user1link = url_username_link(username1)
    user2link = url_username_link(username2)

    to_return = "<a href=" + user1link + ">" +username1+"</a>"+ FOLLOW_TXT + "<a href=" + user2link + ">" +username2+"</a>"

    return to_return
