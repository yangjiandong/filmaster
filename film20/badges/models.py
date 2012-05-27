import re
import logging
logger = logging.getLogger(__name__)

from urlparse import urlparse

from django.conf import settings
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse

from film20.utils.functional import memoize_method
from film20.config.urls import urls
from film20.core.models import Rating, Profile


class Progress(object):
    max = 0
    current = 0

    def __init__(self, value, max):
        self.value = value
        self.max = max

    def percent(self):
        val = min(self.value, self.max)
        return int(round(val * 100.0 / self.max))

    @property
    def left(self):
        return self.max - min(self.value, self.max)


class Goal(object):
    RELOAD_DELAY = 2000

    is_visible = True

    def __init__(self, request):
        self.request = request
        self.user = request.unique_user
        self.name = re.sub("([a-z])([A-Z])", r"\1_\2", self.__class__.__name__).lower()
        self.init()

    def init(self):
        pass

    def info(self):
        return self.render_template('info')

    def progress(self):
        pass

    @classmethod
    def from_request(cls, request):
        user = request.unique_user
        profile = user.id and user.get_profile() or None
        contest = getattr(request, 'contest', False)
        if contest:
            current_goal = 0
        elif profile:
            current_goal = profile.current_goal
        else:
            current_goal = 0

        new_goal = current_goal

        while True:
            goal_cls = GOALS[new_goal] if new_goal < len(GOALS) else Unknown
            goal = goal_cls(request)
            if not goal.is_achieved():
                if profile and new_goal != current_goal:
                    profile.current_goal = new_goal
                    profile.save()
                return goal
            new_goal += 1

    def reload_delay(self):
        return 0

    def get_template_name(self, suffix=''):
        suffix = suffix and '_' + suffix
        return "badges/goals/%s%s.html" % (self.name, suffix)

    def render_template(self, name, ctx=None):
        ctx = ctx or {}
        ctx.update({
            'goal': self,
            'request': self.request,
            'user': self.user,
        })
        return render_to_string(self.get_template_name(name), ctx)

    def state(self):
        return self.name

    def is_achieved(self):
        return False

    def reload_delay(self):
        return self.is_achieved() and self.RELOAD_DELAY or 0


class Unknown(Goal):
    is_visible = False


class InitialRating(Goal):
    @memoize_method
    def progress(self):
        contest = getattr(self.request, 'contest', False)
        if contest:
            return Progress(
                    0,
                    settings.FBAPP['config'].get('movies_to_rate_for_progress', 6)
            )
        return Progress(
                Rating.count_for_user(self.user),
                settings.RECOMMENDATIONS_MIN_VOTES_USER
        )

    def info(self):
        try:
            return self.render_template('info')
        except Exception, e:
            logger.exception(e)
        return ''

    def is_achieved(self):
        return not self.progress().left


class VisitRecommendations(Goal):
    def init(self):
        self.recommendations_status = self.user.id and self.user.get_profile().recommendations_status or 0

    def info(self):
        from film20.utils.utils import is_ajax

        path = self.request.path

        if is_ajax(self.request):
            referer = self.request.META.get('HTTP_REFERER')
            if referer:
                parsed = urlparse(referer)
                path = parsed.path
        
        return self.render_template('info', {
            'recommendations_status': self.recommendations_status,
        })

    def state(self):
        return "%s-%s" % (self.name, self.recommendations_status)

    def is_achieved(self):
        ret = self.recommendations_status in \
                (Profile.NORMAL_RECOMMENDATIONS, Profile.FAST_RECOMMENDATIONS) and \
                self.request.user.is_authenticated() and \
                self.request.path.startswith(reverse('my_recommendations'))
        logger.info("%r %r", ret, self.recommendations_status)
        return ret

    def reload_delay(self):
        if self.is_achieved() or self.recommendations_status == Profile.FAST_RECOMMENDATIONS_WAITING:
            return self.RELOAD_DELAY
        return 0

class RateMoreMovies(Goal):
    @memoize_method
    def progress(self):
        return Progress(
                Rating.count_for_user(self.user),
                1000
        )
    
    def is_achieved(self):
        return not self.progress().left

GOALS = (
        InitialRating,
        VisitRecommendations,
#        RateMoreMovies,
        )

