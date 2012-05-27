"""
pretty

Formats dates, numbers, etc. in a pretty, human readable format.
"""
__author__ = "S Anand (sanand@s-anand.net)"
__copyright__ = "Copyright 2010, S Anand"
__license__ = "WTFPL"

from datetime import datetime

from django.utils.translation import ugettext as _
from django.utils.translation import ngettext

def _df(seconds, denominator=1, text='', past=True):
    if past:   return         str((seconds + denominator/2)/ denominator) + text + _(' ago')
    else:      return 'in ' + str((seconds + denominator/2)/ denominator) + text

def date(time=False, asdays=False, short=False):
    '''Returns a pretty formatted date.
    Inputs:
        time is a datetime object or an int timestamp
        asdays is True if you only want to measure days, not seconds
        short is True if you want "1d ago", "2d ago", etc. False if you want
    '''

    now = datetime.now()
    if type(time) is int:   time = datetime.fromtimestamp(time)
    elif not time:          time = now

    if time > now:  past, diff = False, time - now
    else:           past, diff = True,  now - time
    seconds = diff.seconds
    days    = diff.days

    if short:
        if days == 0 and not asdays:
            if   seconds < 10:          return _('now')
            elif seconds < 60:          return _df(seconds, 1, _('s'), past)
            elif seconds < 3600:        return _df(seconds, 60, _('m'), past)
            else:                       return _df(seconds, 3600, _('h'), past)
        else:
            if   days   == 0:           return _('today')
            elif days   == 1:           return past and _('yest') or _('tom')
            elif days    < 7:           return _df(days, 1, _('d'), past)
            elif days    < 31:          return _df(days, 7, _('w'), past)
            elif days    < 365:         return _df(days, 30, _('mo'), past)
            else:                       return _df(days, 365, _('y'), past)
    else:
        if days == 0 and not asdays:
            if   seconds < 10:          return _('now')
            elif seconds < 60:          return _df(seconds, 1, _(' seconds'), past)
            elif seconds < 120:         return past and _('a minute ago') or _('in a minute')
            elif seconds < 3600:        return _df(seconds, 60, _(' minutes'), past)
            elif seconds < 7200:        return past and _('an hour ago') or _('in an hour')
            else:                       return _df(seconds, 3600, ngettext(' hours', ' hours', 0), past)
        else:
            if   days   == 0:           return _('today')
            elif days   == 1:           return past and _('yesterday') or _('tomorrow')
            elif days   == 2:           return past and _('day before') or _('day after')
            elif days    < 7:           return _df(days, 1, _(' days'), past)
            elif days    < 14:          return past and _('last week') or _('next week')
            elif days    < 31:          return _df(days, 7, _(' weeks'), past)
            elif days    < 61:          return past and _('last month') or _('next month')
            elif days    < 365:         return _df(days, 30, _(' months'), past)
            elif days    < 730:         return past and _('last year') or _('next year')
            else:                       return _df(days, 365, ngettext(' years', ' years', 0), past)
