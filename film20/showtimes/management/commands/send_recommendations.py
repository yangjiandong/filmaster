from optparse import make_option
from decimal import Decimal
import datetime, time, sys

from django.core.management.base import CommandError
from django.db.models import Q, F
from django.conf import settings
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User

from film20.showtimes.models import Town, FilmOnChannel, Screening, EmailTemplate
from film20.filmbasket.models import BasketItem
from film20.showtimes.showtimes_helper import *
from film20.core.management.base import BaseCommand
from film20.notification.models import NoticeType, get_user_media

import logging
logger = logging.getLogger(__name__)

import pytz
import time

class Command(BaseCommand):
#    args = '<location>'
    help = ''
    option_list = BaseCommand.option_list + (
      make_option('--offset',
                  dest='offset',
                  default=0,
                  type='int',
                  help='Start offset (in days)'
      ),
      make_option('--weekly',
                  action='store_true',
                  dest='weekly',
                  default=False,
                  help='Weekly recommendations (daily by default)'
      ),
      make_option('--country',
                  dest='country',
                  default=None,
      ),
      make_option('--debug',
                  action='store_true',
                  dest='debug',
                  default=False,
      ),
      make_option('--site-lang-users',
                  dest='site_lang_users',
                  action='store_true',
                  default=False,
      ),
      make_option('--test',
                  action='store_true',
                  dest='test',
                  default=False,
      ),
      make_option('--days',
                  dest='days',
                  default=0,
                  type='int',
      ),
    )

    def notify(self, *args, **opts):
        users = User.objects.all()
        if opts.get('site_lang_users'):
            users = users.filter(profile__LANG=settings.LANGUAGE_CODE)

        if self.opts['country']:
            users = users.filter(profile__country=self.opts['country'].upper())

        if self.opts['weekly']:
            type_label = 'showtimes_weekly_recommendations'
            days = 7
        else:
            type_label = 'showtimes_daily_recommendations'
            days = 1

        notice_type = NoticeType.objects.get(label=type_label)

        if args:
            users = users.filter(username__in=args)

        date = pytz.utc.localize(datetime.datetime.utcnow()) + datetime.timedelta(days=self.opts['offset'])

        total = users.count()

        for n, user in enumerate(users):
            logger.info("%d/%d - %s",  n+1, total, user)
            if get_user_media(notice_type, user):
                try:
                    self.send_recommendations(user, type_label, date, days)
                except Exception, e:
                    logger.exception(e)

        return

    def send_recommendations(self, user, type_label, date, days):
        from film20.showtimes.showtimes_helper import ScreeningSet

        cinemas = Channel.objects.selected_by(user, Channel.TYPE_CINEMA)
        tv = Channel.objects.selected_by(user, Channel.TYPE_TV_CHANNEL)

        to_date = date + datetime.timedelta(days=days)

        cinema_films = ScreeningSet(date, cinemas, user=user, days=days, without_unmatched=True).get_recommendations()
        tv_films = ScreeningSet(date, tv, user=user, days=days, without_unmatched=True).get_recommendations()

        if not cinema_films and not tv_films:
            logger.debug("no showtimes for %s found (at %s), skipping", user, user.get_profile().location)
            return
        
        def limit(films):
            out = []
            for f in films:
                if f.on_wishlist and len(out) < settings.WEEKLY_RECOMMENDATIONS_MAX_NUMBER_OF_FILMS:
                    out.append(f)
                elif len(out) < settings.WEEKLY_RECOMMENDATIONS_NUMBER_OF_FILMS:
                    out.append(f)
                else:
                    break
            return out

        from film20.notification.models import send

        context = dict(
            cinema_films=limit(cinema_films),
            tv_films=limit(tv_films),
            tv_channels=tv,
            cinemas=cinemas,
            date=date,
            to_date=to_date,
            days=days,
            user=user,
        )
        
        template = EmailTemplate.objects.get_template( 7 if self.opts.get( 'weekly' ) else 1 )
        if template:
            logger.info( "using template: %s" % template )
            context['template'] = template.generate( context )

        if not self.opts.get('test'):
            send([user], type_label, context, now=True)
        else:
            logger.info('test mode, not sending')

    def handle(self, *args, **opts):
        self.opts = opts
        self.logger = logging.getLogger(__name__)
        self.notify(*args, **opts)
