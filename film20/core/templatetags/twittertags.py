import logging
import twitter
logger = logging.getLogger(__name__)

from django import template
from django.utils.translation import ugettext, ugettext_noop
from django.conf import settings
from film20.utils import cache_helper as cache

register = template.Library()

@register.inclusion_tag('home/twitter_activities.html')
def twitter_activity():

    key = cache.Key('twitter_activity')
    tweets = cache.get(key)
    if tweets is None:
        TWEETS_DISPLAYED = getattr(settings, 'TWEETS_DISPLAYED_NUMBER')
        TWITTER_STREAM = getattr(settings, 'TWITTER_STREAM')
        try:
            # Get Filmaster tweets
            tweets = []
            if TWITTER_STREAM:
                api = twitter.Api()
                for tweet in api.GetUserTimeline('Filmaster'):
                    if not '@' in tweet.text:
                        tweets.append(tweet)
                tweets = tweets[:TWEETS_DISPLAYED]
            cache.set(key, tweets)
        except:
            tweets = [{'id': '#', 'text': 'Twitter looks currently down, but don\'t worry about it!'}]
            None # this is fine, we don't want Filmaster to go down in case Twitter goes down

    return {'tweets': tweets}

@register.simple_tag
def tweet_link(id):
    return "http://twitter.com/#!/filmaster/status/" + str(id)

