from film20.core.management.base import BaseCommand
from film20.core.models import Profile
from film20.account.models import OAuthService
import urllib2
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **kw):
        twitter = OAuthService.get_by_name('twitter')
        profiles = Profile.objects.filter(twitter_access_token__gt='', user__username='mrk')
        total = profiles.count()
        for n, profile in enumerate(profiles):
            print "%3s/%s" % (n + 1, total), profile.user.username
            try:
                info = twitter.get_user_info(profile.twitter_access_token)
                print 'ok'
            except urllib2.HTTPError:
                new_token = settings.TWITTER_EXTRA_KEY + '|' + profile.twitter_access_token
                try:
                    info = twitter.get_user_info(new_token)
                    profile.twitter_access_token = new_token
                    profile.save()
                    print 'fixed'
                except urllib2.HTTPError:
                    pass


