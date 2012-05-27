from celery.task.base import Task
from django.utils.translation import activate
from django.conf import settings
from django.db import transaction

import logging
logger = logging.getLogger(__name__)

class DeferredTask(Task):
    def run(self, func, args, kw):
        try:
            activate(settings.LANGUAGE_CODE)
            if not settings.CELERY_ALWAYS_EAGER:
                with transaction.commit_on_success():
                    return func(*args, **kw)
            else:
                return func(*args, **kw)
        except:
            import sys
            self.handle_uncaught_exception(sys.exc_info(), func, args, kw)
            logger.error(sys.exc_info())
            raise

    def handle_uncaught_exception(self, exc_info, *args):
        """
        Borrowed from django.core.handlers.base.BaseHandler
        """

        from django.core.mail import mail_admins

        subject = 'Deferred task error'
        message = u"task: %r\ntrackback:\n%s" % (args, self._get_traceback(exc_info))
        logger.debug("%s: %s", subject, message)
        mail_admins(subject, message, fail_silently=True)

    def _get_traceback(self, exc_info=None):
        "Helper function to return the traceback as a string"
        import traceback
        return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
