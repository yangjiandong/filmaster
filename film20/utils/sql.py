import uuid
import re
from django.utils.html import escape
try:
    # django 1.3 and higher
    from django.core.cache import cache
except ImportError:
    # django 1.2
    from django.utils.cache import cache
from django import http
from django.conf import settings
from django.db import connection
from django.core.urlresolvers import reverse

import logging
sql_logger = logging.getLogger('sql')

class SqlLoggingMiddleware(object):
  def process_request(self, request):
    request.n_queries = len(connection.queries)

  def process_response(self, request, response):
    n = len(connection.queries) - request.n_queries
    if n:
      path = request.get_full_path()
      method = request.method
      queries = list(connection.queries[request.n_queries:])
      total = sum(float(d['time']) for d in queries)
      key = uuid.uuid4()
      cache.set(key, ['http://' + request.get_host() + path, queries])
      sql_view_url = settings.FULL_DOMAIN + reverse("view_sql", args=[key])
      sql_logger.info("%s %s %d quer%s, %s sec, %s",method, path, n, n-1 and "ies" or "y", total, sql_view_url)
    return response

def view_sql(request, key):
    path, queries = cache.get(key) or (None, None)
    if not path or not queries:
        return http.HttpResponse('')
    html = ''.join(sql_to_html(d['sql']) + ("<p class='time'>%s seconds</p>" % d['time']) for d in queries)
    html = """<html>
    <head>
    <link type="text/css" rel="stylesheet" media="all" href="%scss/logging.css" />
    </head>
    <body id="django_log">
    <p>Path: %s</p>%s
    </body>
    </html>""" % (settings.MEDIA_URL, path, html)
    return http.HttpResponse(html)

try:
    import pygments
    import pygments.lexers
    import pygments.formatters
    import pygments.styles
except ImportError:
    pygments = None


def sql_to_html(sql):
    if pygments:
        try:
            lexer = {
                'mysql': pygments.lexers.MySqlLexer,
                }[settings.DATABASE_ENGINE]
        except KeyError:
            lexer = pygments.lexers.SqlLexer
        html = pygments.highlight(sql, lexer(),
            pygments.formatters.HtmlFormatter(cssclass='sql_highlight'))
        
        # Add some line breaks in appropriate places
        html = html.replace('<span class="k">', '<br /><span class="k">')
        html = re.sub(r'(<pre>\s*)<br />', r'\1', html)
        html = re.sub(r'(<span class="k">[^<>]+</span>\s*)<br />(<span class="k">)', r'\1\2', html)
        html = re.sub(r'<br />(<span class="k">(IN|LIKE)</span>)', r'\1', html)
        
        # Add a space after commas to help with wrapping
        html = re.sub(r'<span class="p">,</span>', '<span class="p">, </span>', html)
    
    else:
        html = '<div class="sql_highlight"><pre>%s</pre></div>' % escape(sql)
    
    return html
