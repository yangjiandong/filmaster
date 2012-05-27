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
from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()

# Source: http://www.djangosnippets.org/snippets/12/

class PyIfNode(template.Node):
    def __init__(self, nodeslist):
        self.nodeslist = nodeslist

    def __repr__(self):
        return "<PyIf node>"

    def render(self, context):
        for e, nodes in self.nodeslist:
            clist = list(context)
            clist.reverse()
            d = {}
            d['_'] = _
            for c in clist:
                d.update(c)
            v = eval(e, d)
            if v:
                return nodes.render(context)
        return ''

def do_pyif(parser, token):
    nodeslist = []
    while 1:
        v = token.contents.split(None, 1)
        if v[0] == 'endif':
            break
        if v[0] in ('pyif', 'elif'):
            if len(v) < 2:
                raise template.TemplateSyntaxError, "'pyif' statement requires at least one argument"
        if len(v) == 2:
            tagname, arg = v
        else:
            tagname, arg = v[0], 'True'
        nodes = parser.parse(('else', 'endif', 'elif'))
        nodeslist.append((arg, nodes))
        token = parser.next_token()
#    parser.delete_first_token()
    return PyIfNode(nodeslist)
do_pyif = register.tag("pyif", do_pyif)
