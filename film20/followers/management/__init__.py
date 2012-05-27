from django.db.models import signals

from django.utils.translation import ugettext_noop as _

try:
    from film20.notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("following", _("New follower"), _("New follower"), default=2)

    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
