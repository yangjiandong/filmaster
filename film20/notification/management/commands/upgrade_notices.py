#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
from django.core.management.base import NoArgsCommand
from django.db.models import get_model
from django.utils.translation import ugettext

from notification.models import Notice

# converts pre r70 notices to new approach

def decode_object(ref):
    decoded = ref.split(".")
    if len(decoded) == 4:
        app, name, pk, msgid = decoded
        return get_model(app, name).objects.get(pk=pk), msgid
    app, name, pk = decoded
    return get_model(app, name).objects.get(pk=pk), None

class FormatException(Exception):
    pass

def decode_message(message, decoder):
    out = []
    objects = []
    mapping = {}
    in_field = False
    prev = 0
    for index, ch in enumerate(message):
        if not in_field:
            if ch == '{':
                in_field = True
                if prev != index:
                    out.append(message[prev:index])
                prev = index
            elif ch == '}':
                raise FormatException("unmatched }")
        elif in_field:
            if ch == '{':
                raise FormatException("{ inside {}")
            elif ch == '}':
                in_field = False
                obj, msgid = decoder(message[prev+1:index])
                if msgid is None:
                    objects.append(obj)
                    out.append("%s")
                else:
                    mapping[msgid] = obj
                    out.append("%("+msgid+")s")
                prev = index + 1
    if in_field:
        raise FormatException("unmatched {")
    if prev <= index:
        out.append(message[prev:index+1])
    result = "".join(out)
    if mapping:
        args = mapping
    else:
        args = tuple(objects)
    return ugettext(result) % args

def message_to_html(message):
    def decoder(ref):
        obj, msgid = decode_object(ref)
        if hasattr(obj, "get_absolute_url"):
            return u"""<a href="%s">%s</a>""" % (obj.get_absolute_url(), unicode(obj)), msgid
        else:
            return unicode(obj), msgid
    return decode_message(message, decoder)


class Command(NoArgsCommand):
    help = 'Upgrade notices from old style approach.'
    
    def handle_noargs(self, **options):
        # wrapping in list() is required for sqlite, see http://code.djangoproject.com/ticket/7411
        for notice in list(Notice.objects.all()):
            message = notice.message
            notice.message = message_to_html(message)
            notice.save()

