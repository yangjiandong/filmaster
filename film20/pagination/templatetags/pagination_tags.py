try:
    set
except NameError:
    from sets import Set as set

from django import template
from django.http import Http404
from django.core.paginator import InvalidPage, Paginator
from django.conf import settings
from django.utils.translation import ugettext as _
register = template.Library()

DEFAULT_PAGINATION = getattr(settings, 'PAGINATION_DEFAULT_PAGINATION', 20)
DEFAULT_WINDOW = getattr(settings, 'PAGINATION_DEFAULT_WINDOW', 4)
DEFAULT_ORPHANS = getattr(settings, 'PAGINATION_DEFAULT_ORPHANS', 0)
INVALID_PAGE_RAISES_404 = getattr(settings,
    'PAGINATION_INVALID_PAGE_RAISES_404', False)

### count less pagination
def do_autopaginate(parser, token):
    """
    Splits the arguments to the autopaginate tag and formats them correctly.
    """
    split = token.split_contents()
    as_index = None
    context_var = None
    for i, bit in enumerate(split):
        if bit == 'as':
            as_index = i
            break
    if as_index is not None:
        try:
            context_var = split[as_index + 1]
        except IndexError:
            raise template.TemplateSyntaxError("Context variable assignment " +
                "must take the form of {%% %r object.example_set.all ... as " +
                "context_var_name %%}" % split[0])
        del split[as_index:as_index + 2]
    if len(split) == 2:
        return AutoPaginateNodeNew(split[1])
    elif len(split) == 3:
        return AutoPaginateNodeNew(split[1], paginate_by=split[2],
            context_var=context_var)
    elif len(split) == 4:
        try:
            orphans = int(split[3])
        except ValueError:
            raise template.TemplateSyntaxError(u'Got %s, but expected integer.'
                % split[3])
        return AutoPaginateNodeNew(split[1], paginate_by=split[2], orphans=orphans,
            context_var=context_var)
    else:
        raise template.TemplateSyntaxError('%r tag takes one required ' +
            'argument and one optional argument' % split[0])

class AutoPaginateNodeNew(template.Node):
    """
    Emits the required objects to allow for Digg-style pagination.

    First, it looks in the current context for the variable specified, and using
    that object, it emits a simple ``Paginator`` and the current page object
    into the context names ``paginator`` and ``page_obj``, respectively.

    It will then replace the variable specified with only the objects for the
    current page.

    .. note::

        It is recommended to use *{% paginate %}* after using the autopaginate
        tag.  If you choose not to use *{% paginate %}*, make sure to display the
        list of available pages, or else the application may seem to be buggy.
    """
    def __init__(self, queryset_var, paginate_by=DEFAULT_PAGINATION,
        orphans=DEFAULT_ORPHANS, context_var=None):
        self.queryset_var = template.Variable(queryset_var)
        if isinstance(paginate_by, int):
            self.paginate_by = paginate_by
        else:
            self.paginate_by = template.Variable(paginate_by)
        self.orphans = orphans
        self.context_var = context_var

    def render(self, context):
        key = self.queryset_var.var
        value = self.queryset_var.resolve(context)
        if isinstance(self.paginate_by, int):
            paginate_by = self.paginate_by
        else:
            paginate_by = self.paginate_by.resolve(context)
        from film20.pagination.paginator import InfinitePaginator
        paginator = InfinitePaginator (value, paginate_by, self.orphans)
        try:
            page_obj = paginator.page(context['request'].page)
        except InvalidPage:
            if INVALID_PAGE_RAISES_404:
                raise Http404('Invalid page requested.  If DEBUG were set to ' +
                    'False, an HTTP 404 page would have been shown instead.')
            context[key] = []
            context['invalid_page'] = True
            return u''

        context[self.context_var or key] = page_obj.object_list

        context['paginator'] = paginator
        context['page_obj'] = page_obj
        context['page'] = context['request'].page
        return u''

@register.inclusion_tag('pagination/old_pagination.html', takes_context=True)
def paginator(context, show_all=None, window=DEFAULT_WINDOW):
    try:
        paginator = context['paginator']
        page_obj = context['page_obj']
        page = context['page']
        to_return = {
            'MEDIA_URL': settings.MEDIA_URL,
            'page_obj': page_obj,
            'paginator': paginator,
            'page': page,
        }
        if ((show_all == 'show_all')):
            is_showing_all = context['is_showing_all']
            showing = {
                'is_showing_all':is_showing_all,
                'show_all' : show_all,
            }
            to_return.update(showing)

        request = context.get('request')

        if request:
            page_key = _('page')
            def _path(page_nr):
                params = request.GET.copy()
                if page_key in params:
                    del params[page_key]
                params[page_key] = page_nr
                return params.urlencode()

            if page_obj.has_previous():
                to_return['prev_path'] = _path(page_obj.previous_page_number())
            if page_obj.has_next():
                to_return['next_path'] = _path(page_obj.next_page_number())
                
        return to_return
    except KeyError, AttributeError:
        return {}

register.tag('autopaginate', do_autopaginate)

# TODO - for backward compatibility, remove
register.tag('autopaginate_new', do_autopaginate)
@register.inclusion_tag('pagination/old_pagination.html', takes_context=True)
def paginate_new(context, show_all=None, window=DEFAULT_WINDOW):
    return paginator(context, show_all, window)

