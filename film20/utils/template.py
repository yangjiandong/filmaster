from django import template
from django.conf import settings
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse, NoReverseMatch

from film20.core.urlresolvers import make_absolute_url

import re
import logging
logger = logging.getLogger(__name__)

class Library(template.Library):
    def setcontexttag(self, func):
        name = func.__name__

        @self.tag(name=name)
        def parse(parser, token):
            bits = token.split_contents()
            args = [parser.compile_filter(bit) for bit in bits]
            nodelist = parser.parse(('end' + name,))
            parser.delete_first_token()
            return SetContextNode(func, args, nodelist)

    def widget(self, template_path, param_conv=None, embed=False):
        def dec(func):
            name = func.__name__
            @self.tag(name=name)
            def parse(parser, token):
                bits = token.split_contents()
                args = [parser.compile_filter(bit) for bit in bits]
                if embed:
                    return WidgetNode(func, template_path, args)
                else:
                    return AjaxWidgetNode(name, func, template_path, args, param_conv)
            class WidgetView(BaseWidgetView):
                template_name = template_path
            WidgetView.func = [func]
            self._widget_views = getattr(self, '_widget_views', {})
            self._widget_views[name] = WidgetView

            return func
        return dec

    def get_widget_view(self, name):
        return self._widget_views[name].as_view()

    KWARGS_RE = re.compile(r"(?:(\w+)=)?(.+)")
    def new_inclusion_tag(self, template_name):
        def dec(func):
            name = func.__name__
            @self.tag(name=name)
            def parse(parser, token):
                kwargs = {}
                args = []
                bits = token.split_contents()
                for bit in bits[1:]:
                    match = self.KWARGS_RE.match(bit)
                    if not match:
                        raise TemplateSyntaxError("Malformed arguments")
                    name, value = match.groups()
                    if name:
                        kwargs[name] = parser.compile_filter(value)
                    else:
                        args.append(parser.compile_filter(value))
                return NewInclusionTagNode(name, func, template_name, args, kwargs)
            return func
        return dec

class SetContextNode(template.Node):
    def __init__(self, func, args, nodelist):
        self.func = func
        self.args = args[1:]
        self.nodelist = nodelist

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        context.push()
        context.update(self.func(*args))
        out = self.nodelist.render(context)
        context.pop()
        return out

from django.template.loader import render_to_string
class WidgetNode(template.Node):
    def __init__(self, func, template_path, args):
        self.func = func
        self.template_path = template_path
        self.args = args[1:]

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        context.push()
        ctx = self.func(context.get('request'), *args)
        context.update(ctx)
        out = render_to_string(self.template_path, context_instance=context)
        context.pop()
        return out

class AjaxWidgetNode(template.Node):
    def __init__(self, name, func, template_path, args, param_conv):
        self.name = name
        self.func = func
        self.template_path = template_path
        self.args = args[1:]
        self.param_conv = param_conv

    def render(self, context):
        import cgi, json
        from urllib import urlencode
        from django.core.urlresolvers import reverse
        request = context['request']
        widget_cnt = getattr(request, 'widget_cnt', 1)
        args = [arg.resolve(context) for arg in self.args]
        args = self.param_conv and urlencode(self.param_conv(*args)) or ''
        
        name = self.name
        library = self.func.__module__.split('.')[-1]
        
        out = """<div class="ajax-widget" id="widget-%(widget_cnt)d" data-url="%(url)s"></div>""" % dict(
                widget_cnt=widget_cnt,
                url=reverse('ajax_widget', args=[library, name]) + '?' + args,
        )
        request.widget_cnt = widget_cnt + 1
        return out

from django.views.generic.base import TemplateView

class BaseWidgetView(TemplateView):
    def get_context_data(self, **kw):
        context = super(BaseWidgetView, self).get_context_data(**kw)
        context.update(self.func[0](self.request))
        return context

class NewInclusionTagNode(template.Node):
    def __init__(self, name, func, template_path, args, kwargs):
        self.name = name
        self.func = func
        self.template_path = template_path
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict((k, v.resolve(context)) for (k, v) in self.kwargs.items())
        context.push()
        context.update(self.func(context, *args, **kwargs))
        out = render_to_string(self.template_path, context_instance=context)
        context.pop()
        return out

