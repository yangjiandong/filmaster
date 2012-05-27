from django.contrib import admin
from models import FilmOnChannel, Country, Town, Screening, Channel, Fetcher, EmailTemplate
from forms import FilmOnChannelForm
from django.contrib.admin.filterspecs import FilterSpec
import datetime
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.translation import gettext_lazy as _

def rematch(modeladmin, request, queryset):
    for f in queryset.all():
        f.match_and_save()

rematch.short_description = u"match selected films"

class HasImdbCodeFilterSpec(FilterSpec):
  def __init__(self, f, request, params, model, model_admin, **kw):
    super(HasImdbCodeFilterSpec, self).__init__(f, request, params, model, model_admin, **kw)
    self.current_params = dict((k, v) for k, v in params.items() if (k.startswith("imdb_code" or k.startswith("id__gt"))))
    self.links = (('Wszystko', {}),
                  ('Bez imdb code',{'imdb_code__isnull':'true'}),
                  ('Z imdb code',{"imdb_code__isnull":''}),
                 )
            
  def choices(self,cl):
    return ({'selected':params == self.current_params, 
            'query_string':cl.get_query_string(params, ["imdb_code"]),
            'display':title,
            } for title, params in self.links)
    
  def title(self): return u"imdb_code"

class CurrentlyPlayingFilterSpec(FilterSpec):
    _params = ["screening__channel__country__code", "screening__utc_time__gt"]
    def __init__(self, f, request, params, model, model_admin, **kw):
        super(CurrentlyPlayingFilterSpec, self).__init__(f, request, params, model, model_admin, **kw)
        self.current_params = dict((k, v) for k, v in params.items() if any(k.startswith(i) for i in self._params))
        self.links = [(_('All'), {})]
        today = str(datetime.date.today())
        self.links.extend((code, {
            'screening__channel__country__code': code, 
            'screening__utc_time__gt': today
        }) for code in settings.COUNTRIES_WITH_SHOWTIMES)

    def choices(self,cl):
        return ({'selected':params == self.current_params, 
                'query_string':cl.get_query_string(params, self._params),
                'display':title,
                } for title, params in self.links)
    
    def title(self):
        return _(u"Currently playing in")

class ChannelTypeFilterSpec(FilterSpec):
    _params = ["screening__channel__type"]
    def __init__(self, f, request, params, model, model_admin, **kw):
        super(ChannelTypeFilterSpec, self).__init__(f, request, params, model, model_admin, **kw)
        self.current_params = dict((k, v) for k, v in params.items() if any(k.startswith(i) for i in self._params))
        self.links = [
                (_('All'), {}),
                (_('Theaters'), {'screening__channel__type': '1', }),
                (_('TV'), {'screening__channel__type': '2', })
        ]

    def choices(self,cl):
        return ({'selected':params == self.current_params, 
                'query_string':cl.get_query_string(params, self._params),
                'display':title,
                } for title, params in self.links)
    
    def title(self):
        return _(u"Channel type")

from django.contrib.admin.views.main import ChangeList as ChangeListOrig
class ChangeList(ChangeListOrig):
    def get_query_set(self, *args, **kw):
        qs = super(ChangeList, self).get_query_set(*args, **kw)
        if self.model_admin.distinct(self.params):
            qs = qs.distinct()
        order_by = self.params.get('o')
        ordering = self.model_admin.ordering
        if not order_by and ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_filters(self, request):
        filters, _ = super(ChangeList, self).get_filters(request)
        filters.extend(
                spec('', request, self.params, self.model,
                     self.model_admin, field_path='') for spec in self.model_admin.extra_list_filter
                )
        return filters, bool(filters)

class ModelAdmin(admin.ModelAdmin):
    extra_list_filter = ()

    def lookup_allowed(self, lookup, value=None):
        return True
    
    def get_changelist(self, request, **kwargs):
        return ChangeList
    
    def distinct(self, params):
        return False

def _film_on_channel_title(obj):
    if obj.source == 'facebook':
        return '<a href="%s">%s</a>' % (obj.key, obj.title or '[link]')
    return obj.title

_film_on_channel_title.allow_tags = True
_film_on_channel_title.__name__ = 'title'

class FilmOnChannelAdmin(ModelAdmin):
    list_display = ('key', _film_on_channel_title, 'match', 'priority')
    raw_id_fields = ('film',)
    list_filter = ('match', 'source', 'created_at')
    extra_list_filter = (CurrentlyPlayingFilterSpec, ChannelTypeFilterSpec, HasImdbCodeFilterSpec, )
    ordering = ('-priority', '-id')
    search_fields = ('title', 'directors')
    distinct = True
    
    form = FilmOnChannelForm

    actions = [rematch]

    def distinct(self, params):
        return any(k.startswith('screening__') for k in params.keys())

class ScreeningAdmin(ModelAdmin):
    list_display = ('id', 'film', 'channel', 'utc_time')
    list_filter = ('channel__name', 'channel__type', )
    raw_id_fields = ('film', 'channel')
    search_fields = ('channel__name',)

class FetcherInline(admin.TabularInline):
    model = Fetcher

def last_screening_time(obj):
    tm = obj.last_screening_time
    if tm and tm < datetime.datetime.now():
        style = "font-weight:bold; color:red"
    else:
        style = ""
    return mark_safe("<span style='%s'>%s</span>" % (style, tm or ''))
last_screening_time.allow_tags = True

class ChannelAdmin(ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'town', 'is_active', last_screening_time)
    list_filter = ('is_active', 'type', 'country', 'town')
    ordering = ('name', )
    
    inlines = [FetcherInline]

    @classmethod
    def enable(cls, modeladmin, request, queryset):
        for item in queryset:
            item.is_active = True
            item.save()

    @classmethod
    def disable(cls, modeladmin, request, queryset):
        for item in queryset:
            item.is_active = False
            item.save()

    actions = ['enable', 'disable']

class CountryAdmin(ModelAdmin):
    ordering = ('name',)

class TownAdmin(ModelAdmin):
    ordering = ('name',)
    list_filter = ('country', )

admin.site.register(FilmOnChannel, FilmOnChannelAdmin)
admin.site.register(Screening, ScreeningAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Town, TownAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(EmailTemplate)
