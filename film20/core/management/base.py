import logging
import itertools
from django.core.management import base
from django.core.management.base import CommandError
from django.utils.translation import gettext
from optparse import make_option

gettext("foo") # circular dependency workaround

class BaseCommand(base.BaseCommand):
    _LEVELS = (logging.WARNING, logging.INFO, logging.DEBUG)

    def execute(self, *args, **opts):
        # set console level according to verbosity
        for h in itertools.chain(logging.getLogger('film20').handlers, logging.getLogger().handlers):
            if isinstance(h, logging.StreamHandler):
                h.level = self._LEVELS[int(opts.get('verbosity',0))]
        super(BaseCommand, self).execute(*args, **opts)
        
