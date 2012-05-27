from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from django.template.context import RequestContext

from film20.useractivity.models import UserActivity
from film20.config.urls import templates, urls
from film20.useractivity.useractivity_helper import ajax_activity_pager, \
    ajax_select_template

from film20.useractivity.views import WallView

class PublicProfileView(WallView):
    template_name = templates['PROFILE']

    def get(self, request, username, activity_option):
        self.activity_option = activity_option
        self.username = username
        self.user = get_object_or_404(User.objects, username__iexact=username)
        return super(PublicProfileView, self).get(request)

    def get_activities(self):
        if self.activity_option == 'user_all':
            activities = UserActivity.objects.all_for_user(self.user)
        else:
            activities = UserActivity.objects.public()
        if not self.is_filtered:
            activities = activities.filter( hidden=False )
        return activities

    def get_context_data(self, **kw):
        context = super(PublicProfileView, self).get_context_data(**kw)
        context['user_profile'] = self.user
        return context

public_profile = PublicProfileView.as_view()

def _public_profile(request, username, activity_option):
    """
        Show public user profile
    """
    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404

    if activity_option == 'user_all':
        activities = UserActivity.objects.all_for_user(user)
    else:
        activities = UserActivity.objects.public()

    activities = ajax_activity_pager(request, activities)
    
    data = {
        'activities': activities,
        'user_profile': user,
    }

    return render(
        request,
        ajax_select_template(request, templates['PROFILE']),
        data
    )


def show_article(request, username, permalink):
    """
       Show article for given username and permalink
    """

    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404

    try:
        # there should be always only one of those
        article = UserActivity.objects.select_related().get(
            username__iexact = username,
            post__permalink = permalink,
            status = UserActivity.PUBLIC_STATUS)
    except UserActivity.DoesNotExist:
        # check for draft articles
        articles = UserActivity.objects.select_related().filter(
            username__iexact = username, 
            post__permalink = permalink,
            status = UserActivity.DRAFT_STATUS)
        if len(articles)==0:
            raise Http404
        else:
            article = articles[0] 
        # show draft only if currently logged in user is viewing
        if (not request.user.is_superuser) and (request.user != user):
            raise Http404

    data = {
        'activity' : article,
        'user_profile': user,
    }

    return render(
        request,
        templates['ARTICLE'],
        data,
    )

def show_wall_post(request, username, post_id):
    """
       Show wall post for given id
    """

    try:
        wall_post = UserActivity.objects.select_related().get(
            short_review__id = post_id,
            username__iexact = username,
            status = UserActivity.PUBLIC_STATUS)
    except UserActivity.DoesNotExist:
        raise Http404

    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404

    data = {
        'activity' : wall_post,
        'user_profile': user
    }

    return render(
        request,
        templates['WALL_POST'],
        data,
    )

def show_followed(request, username):
    """
        Show users followed by a user
    """
    
    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404

    followers = user.followers.followers()

    data = {
        'users' : followers,
        'user_profile': user
    }

    return render(
        request,
        templates['PROFILE_FOLLOWED'],
        data,
    )


def show_followers(request, username):
    """
        Show userse following user
    """

    try:
        user = User.objects.get(username__iexact=username)
    except User.DoesNotExist:
        raise Http404

    following = user.followers.following()

    data = {
        'users' : following,
        'user_profile': user
    }

    return render(
        request,
        templates['PROFILE_FOLLOWERS'],
        data,
    )

from django.views.generic.detail import DetailView
from film20.core.views import UsernameMixin

class ActivityView(UsernameMixin, DetailView):
    context_object_name = 'activity'

    def get_context_data( self, **kwargs ):
        context = super( ActivityView, self ).get_context_data( **kwargs )
        context['show_single'] = True
        context['activity_view'] = True
        return context

    def get_object(self):
        field = UserActivity.OBJECT_FIELD_MAP.get(self.activity_type, 'id')
        return get_object_or_404(
                UserActivity.objects.public(),
                activity_type=self.activity_type,
                username__iexact=self.kwargs.get('username'),
                **{field: self.kwargs.get('id')})
    

class CheckinView(ActivityView):
    activity_type = UserActivity.TYPE_CHECKIN
    template_name = 'profile/checkin.html'

show_checkin = CheckinView.as_view()

class RatingView(ActivityView):
    activity_type = UserActivity.TYPE_RATING
    template_name = 'profile/rating.html'

show_rating = RatingView.as_view()

class LinkView(ActivityView):
    activity_type = UserActivity.TYPE_LINK
    template_name = 'profile/link.html'

show_link = LinkView.as_view()

class PosterView(ActivityView):
    activity_type = UserActivity.TYPE_POSTER
    template_name = 'profile/poster.html'

show_poster = PosterView.as_view()

class DemotView(ActivityView):
    activity_type = UserActivity.TYPE_DEMOT
    template_name = 'profile/demot.html'

show_demot = DemotView.as_view()

class TrailerView(ActivityView):
    activity_type = UserActivity.TYPE_TRAILER
    template_name = 'profile/trailer.html'

show_trailer = TrailerView.as_view()

