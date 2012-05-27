from django.core.mail import EmailMessage
from django.views.debug import ExceptionReporter
from django.core import exceptions
from django.conf import settings
from django import http
import sys
import logging
logger = logging.getLogger(__name__)

class ExceptionMailer(object):
    def process_exception(self, request, exception):
        if settings.DEBUG_PROPAGATE_EXCEPTIONS or settings.DEBUG or isinstance(exception, (SystemExit, exceptions.PermissionDenied, http.Http404)):
            return

        exc_type, exc_value, tb = sys.exc_info()
        reporter = ExceptionReporter(request, exc_type, exc_value, tb.tb_next)
        subject = 'Detailed Error (%s IP): %s' % ((request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)

        html = reporter.get_traceback_html()

        message = EmailMessage(settings.EMAIL_SUBJECT_PREFIX+subject,
                                html, settings.SERVER_EMAIL,
                                [ admin[1] for admin in settings.ADMINS ])

        message.content_subtype = 'html'
        message.send(fail_silently=True)

from django.db import connection, reset_queries
from django import db
import os

class RequestStatsMiddleware(object):
    def process_request(self, request):
        db.connection.use_debug_cursor=True
        db.reset_queries()
        request._times = os.times()

    def process_response(self, request, response):
        if not hasattr(request, '_times'):
            return response
        times = os.times()
        delta = [int((b - a)*1000) for (a, b) in zip(request._times, times)]
        total = delta[4]
        n = len(connection.queries)
        if total >= settings.REQUEST_TIME_WARNING_THRESHOLD or n >= settings.NUM_QUERIES_WARNING_THRESHOLD:
            queries_time = sum(float(q['time']) for q in db.connection.queries) * 1000
            logger.warning("%s%s - time: %d ms %r, %d queries (%d ms)", request.get_host(), request.path, total, delta, n, queries_time)
        elif n:
            logger.debug("%s%s - time: %d ms %r, %d queries", request.get_host(), request.path, total, delta, n)
        return response

