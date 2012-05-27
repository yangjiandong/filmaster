import logging
logger = logging.getLogger(__name__)
import datetime
from optparse import make_option
import urllib2

from film20.core.management.base import BaseCommand
from film20.facebook_connect.models import FBAssociation, FBUser
from film20.facebook_connect import graph

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--initial',
                action='store_true',
                dest='initial',
                default=False,
        ),
        make_option('--all',
                action='store_true',
                dest='all',
                default=False,
        ),
        make_option('--fix-associations',
                action='store_true',
                dest='fix_associations',
                default=False,
        ),
        make_option('--limit',
                type='int',
                dest='limit',
        ),
    )

    def fix_associations(self):
        api = graph.API()
        query = FBAssociation.objects.filter(fb_user__isnull=True)
        total = query.count()
        for n, assoc in enumerate(query):
            logger.info(assoc.fb_uid)
            try:
                user_data = api.get("/%s" % assoc.fb_uid)
            except urllib2.HTTPError, e:
                logger.warning(unicode(e))
                continue
            logger.info("%d / %d %r", n+1, total, user_data)
            if user_data:
                assoc.fb_user = FBUser.create_or_update(user_data)
            else:
                assoc.fb_user = FBUser.objects.create(id=assoc.fb_uid)
            assoc.save()

    def handle(self, *args, **opts):
        if opts.get('fix_associations'):
            self.fix_associations()
            return
        limit = opts.get('limit')
        query = FBAssociation.objects.all()
#        to_date = datetime.datetime.now() - datetime.timedelta(days=1)
#        query = query.filter(updated_at__lt=to_date)
        query = query.order_by('updated_at')
        if opts.get('initial'):
            query = query.filter(status=0)
        elif not opts.get('all'):
            query = query.filter(status__lte=1)
        if args:
            query = query.filter(user__username__in=args)
        if limit:
            query = query[:limit]
        for assoc in query:
            assoc.sync_with_fb()
            logger.info("%20s: %s", assoc, assoc.status==1 and "OK" or assoc.status)

