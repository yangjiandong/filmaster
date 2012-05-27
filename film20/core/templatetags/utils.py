from django import template
from django.conf import settings
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse, NoReverseMatch


from film20.core.urlresolvers import make_absolute_url

import re
import logging
logger = logging.getLogger(__name__)

register = template.Library()

class ANode(template.Node):
    def __init__(self, view, args, kwargs, nodelist, match_prefix=False):
        self.view = view
        self.args = args
        self.kwargs = kwargs
        self.nodelist = nodelist
        if match_prefix:
            self.match_func = lambda a, b: a.startswith(b)
        else:
            self.match_func = lambda a, b: a==b

    def render(self, context):
        from django.utils.http import urlquote
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        
        try:
            path = reverse(self.view, args=args, kwargs=kwargs)
            qpath = urlquote(path)
        except NoReverseMatch, e:
            raise e

        request = context.get('request')
        if request and any(self.match_func(urlquote(p), path) for p in (request.path, request.path_info)):
            cls = ' class="selected"'
        else:
            cls = ''
        
        out = ['<a href="%s"%s>' % (make_absolute_url(path), cls)]
        out.append(self.nodelist.render(context))
        out.append('</a>')

        return ''.join(out)

# borrowed from django
kwarg_re = re.compile(r"(?:(\w+)=)?(.+)")
class URLNode(template.Node):
    def __init__(self, view_name, args, kwargs, asvar, legacy_view_name=True, absolute=True):
        self.view_name = view_name
        self.legacy_view_name = legacy_view_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar
        self.absolute = absolute

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        view_name = self.view_name
        if not self.legacy_view_name:
            view_name = view_name.resolve(context)

        # Try to look up the URL twice: once given the view name, and again
        # relative to what we guess is the "main" app. If they both fail,
        # re-raise the NoReverseMatch unless we're using the
        # {% url ... as var %} construct in which cause return nothing.
        url = ''
        try:
            url = reverse(view_name, args=args, kwargs=kwargs, current_app=context.current_app)
        except NoReverseMatch, e:
            if settings.SETTINGS_MODULE:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                try:
                    url = reverse(project_name + '.' + view_name,
                              args=args, kwargs=kwargs,
                              current_app=context.current_app)
                except NoReverseMatch:
                    if self.asvar is None:
                        # Re-raise the original exception, not the one with
                        # the path relative to the project. This makes a
                        # better error message.
                        raise e
            else:
                if self.asvar is None:
                    raise e

        if self.absolute:
            request = context.get('request')
            secure = request and request.META.get('SERVER_PORT') == '443'
            url = make_absolute_url(url, secure)

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url

def _parse(parser, token):
    """
    Returns an absolute URL matching given view with its parameters.

    This is a way to define links that aren't tied to a particular URL
    configuration::

        {% url path.to.some_view arg1 arg2 %}

        or

        {% url path.to.some_view name1=value1 name2=value2 %}

    The first argument is a path to a view. It can be an absolute python path
    or just ``app_name.view_name`` without the project name if the view is
    located inside the project.  Other arguments are comma-separated values
    that will be filled in place of positional and keyword arguments in the
    URL. All arguments for the URL should be present.

    For example if you have a view ``app_name.client`` taking client's id and
    the corresponding line in a URLconf looks like this::

        ('^client/(\d+)/$', 'app_name.client')

    and this app's URLconf is included into the project's URLconf under some
    path::

        ('^clients/', include('project_name.app_name.urls'))

    then in a template you can create a link for a certain client like this::

        {% url app_name.client client.id %}

    The URL will look like ``/clients/client/123/``.
    """

    import warnings
    warnings.warn('The syntax for the url template tag is changing. Load the `url` tag from the `future` tag library to start using the new behavior.',
                  category=PendingDeprecationWarning)

    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    viewname = bits[1]
    args = []
    kwargs = {}
    asvar = None
    matchprefix = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]
    if len(bits) >= 1 and bits[-1] == 'match_prefix':
        matchprefix = True
        bits = bits[:-1]

    # Backwards compatibility: check for the old comma separated format
    # {% url urlname arg1,arg2 %}
    # Initial check - that the first space separated bit has a comma in it
    if bits and ',' in bits[0]:
        check_old_format = True
        # In order to *really* be old format, there must be a comma
        # in *every* space separated bit, except the last.
        for bit in bits[1:-1]:
            if ',' not in bit:
                # No comma in this bit. Either the comma we found
                # in bit 1 was a false positive (e.g., comma in a string),
                # or there is a syntax problem with missing commas
                check_old_format = False
                break
    else:
        # No comma found - must be new format.
        check_old_format = False

    if check_old_format:
        # Confirm that this is old format by trying to parse the first
        # argument. An exception will be raised if the comma is
        # unexpected (i.e. outside of a static string).
        match = kwarg_re.match(bits[0])
        if match:
            value = match.groups()[1]
            try:
                parser.compile_filter(value)
            except TemplateSyntaxError:
                bits = ''.join(bits).split(',')

    # Now all the bits are parsed into new format,
    # process them as template vars
    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return (viewname, args, kwargs, asvar, matchprefix, True)

@register.tag
def url(parser, token):
    viewname, args, kwargs, asvar, _, legacy_view_name = _parse(parser, token)
    return URLNode(viewname, args, kwargs, asvar, legacy_view_name=True)

@register.tag
def relurl(parser, token):
    viewname, args, kwargs, asvar, _, legacy_view_name = _parse(parser, token)
    return URLNode(viewname, args, kwargs, asvar, legacy_view_name=True, absolute=False)

@register.tag
def a(parser, token):
    viewname, args, kwargs, _, matchprefix, legacy_view_name = _parse(parser, token)
    nodelist = parser.parse(('enda',))
    parser.delete_first_token()
    return ANode(viewname, args, kwargs, nodelist, matchprefix)

class ActionFormNode(template.Node):
    def __init__(self, view_name, args, kwargs, node_list):
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.node_list = node_list

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        class_arg = kwargs.pop('class')
        class_arg = class_arg and (" " + class_arg)

        rev_kw = dict( i for i in kwargs.items() if not i[0].startswith('input_'))

        try:
            action = reverse(self.view_name, args=args, kwargs=rev_kw, current_app=context.current_app)
        except NoReverseMatch, e:
            raise e
        
        inputs = ["<input type='hidden' name='%s' value='%s' />" % (k[6:], v) for k, v in kwargs.items() if k.startswith('input_')]
                    
        return """
            <form class="actionform%(class_arg)s" method="POST" action="%(action)s">
            %(inputs)s
            <input type="submit" value="%(submit_value)s">
            </form>
        """ % dict(
            action=action,
            inputs=''.join(inputs),
            submit_value=self.node_list.render(context),
            class_arg=class_arg,
        )

@register.tag
def actionform(parser, token):
    viewname, args, kwargs, _, matchprefix, legacy_view_name = _parse(parser, token)
    node_list = parser.parse(('endactionform', ))
    parser.delete_first_token()
    return ActionFormNode(viewname, args, kwargs, node_list)

