import logging
logger = logging.getLogger(__name__)

from django.db.models.sql.datastructures import EmptyResultSet
from django.db import models
from django.db.models.query import RawQuerySet
from django.conf import settings

from film20.utils import cache_helper as cache

# http://www.djangosnippets.org/snippets/562/#c673
class QuerySetManager(models.Manager):
    # http://docs.djangoproject.com/en/dev/topics/db/managers/#using-managers-for-related-object-access
    # Not working cause of:
    # http://code.djangoproject.com/ticket/9643
    use_for_related_fields = False
    def __init__(self, qs_class=models.query.QuerySet, related_manager=False):
        self.queryset_class = qs_class
        self.related_manager = related_manager
        super(QuerySetManager, self).__init__()

    def get_query_set(self):
        query_set = self.queryset_class(self.model)
        if hasattr(query_set, 'default_filter') and not self.related_manager:
            query_set = query_set.default_filter()
        return query_set

    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            if attr.startswith('__'): 
                raise
            return getattr(self.get_query_set(), attr, *args)

    def raw(self, raw_query, params=None, *args, **kwargs):
        return EnhancedRawQuerySet(raw_query=raw_query, model=self.model, params=params, using=self._db, *args, **kwargs)

#    def none(self):
#        class _EmptyQuerySet(self.queryset_class):
#            def iterator(self):
#                return iter(())
#
#        return _EmptyQuerySet(self.model)

class QuerySet(models.query.QuerySet):
    """Base QuerySet class for adding custom methods that are made
    available on both the manager and subsequent cloned QuerySets"""

    @classmethod
    def as_manager(cls, ManagerClass=QuerySetManager):
        class _tmp(ManagerClass):
            def __init__(self, related_manager=True):
                super(_tmp, self).__init__(cls, related_manager)
        return _tmp(related_manager=False)

    # make sense only for models with latitude and longitude fields of course
    def nearby(self, lat, lon, radius=50):
        table = self.model._meta.db_table
        distance = """6371 * 2 * ASIN(SQRT(POWER(SIN((ABS(%%s) - ABS("%(table)s"."latitude")) * pi()/180 / 2), 2) + \
                      COS(%%s * pi()/180 ) * COS(abs("%(table)s"."latitude") * pi()/180) * POWER(SIN((%%s-"%(table)s"."longitude") * pi()/180 / 2), 2)))""" % dict(table=table)
        params = [lat, lat, lon]
        return self.extra(select={'distance':distance},
                        select_params=params,
                        where = ['%s < %%s' % distance],
                        params = params + [radius],
                        order_by=['distance', 'name'],
               )

    def random(self):
        return self.order_by("?")

    def first(self):
        return self[0]

    def postprocess_query(self, iterator, **kw):
        post_func = getattr(self, 'post_func', ()) or ()
        for func in post_func:
            iterator = func(iterator, **kw)
        return iterator

    def _make_key(self):
        cache_prefix, cache_timeout= getattr(self, 'cache_params', (None, None))
        if cache_prefix:
            try:
                return cache.Key(cache_prefix, str(self.query))
            except EmptyResultSet, e:
                return cache.Key(cache_prefix, "emptyresult", self.model)
            
    def iterator(self):
        items = super(QuerySet, self).iterator()
        cache_prefix, cache_timeout = getattr(self, 'cache_params', (None, None))
        cache_key = self._make_key()
        
        if cache_key:
            result = cache.get(cache_key)
            if result is None:
                result = list(items)
                cache.set(cache_key, result, cache_timeout)
            items = iter(result)
        return self.postprocess_query(items)
        
    def sorted(self, *args, **kw):
        def sort(iterator, **_kw):
            return iter(sorted(iterator, *args, **kw))
        return self.postprocess(sort)
    
    def cache(self, prefix=None, timeout=None):
        return self
        prefix = prefix or ("%s_cached_query" % self.model.__name__.lower())
        return self._clone(cache_params=(prefix, timeout))
        
    def invalidate(self):
        cache_prefix, cache_timeout = getattr(self, 'cache_params', (None, None))
        cache_key = self._make_key()
        if cache_key:
            # give a chance to postprocess function to invalidate internal caches
            self.postprocess_query(iter(self), invalidate_cache=True)
            cache.delete(cache_key)
            return True
        logger.warning("invalidate without cache")
        return False
    
    def postprocess(self, func):
        return self
        return self._clone(post_func=getattr(self, 'post_func', []) + [func])
        
    def _clone(self, *args, **kw):
        ret = super(QuerySet, self)._clone(*args, **kw)
        for attr in ('cache_params', 'post_func'):
            if not hasattr(ret, attr) and hasattr(self, attr):
                setattr(ret, attr, getattr(self, attr))
        return ret

    def __getstate__(self):
        """
        Allows the QuerySet to be pickled.
        """
        obj_dict = super(QuerySet, self).__getstate__()
        obj_dict['post_func'] = ()
        return obj_dict

class LangQuerySet(QuerySet):
    def default_filter(self):
        return self.filter(LANG=settings.LANGUAGE_CODE)

import re

class EnhancedRawQuerySet(RawQuerySet):
    INF = 2**64 # greatly simplifies calculations
    LIMIT_RE = re.compile(r"limit\s+(\d+)")
    OFFSET_RE = re.compile(r"offset\s+(\d+)")

    def parse_limits(self):
        m = self.OFFSET_RE.search(self.raw_query)
        start = m and int(m.group(1)) or 0
        
        m = self.LIMIT_RE.search(self.raw_query)
        if m:
            stop = m and start + int(m.group(1))
        else:
            stop = self.INF
        
        query = self.OFFSET_RE.sub("", self.LIMIT_RE.sub("", self.raw_query)).strip()

        return start, stop, query            
        

    def __getitem__(self, k):
        cur_start, cur_stop, new_query = self.parse_limits()
        
        if isinstance(k, slice):
            start = k.start or 0
            stop = k.stop if k.stop is not None else self.INF
        elif isinstance(k, (int, long)):
            start = k
            stop = k+1
        else:
            raise TypeError
        
        new_start = min(cur_start + start, cur_stop)
        new_stop = min(cur_start + stop, cur_stop)
        
        if new_start:
            new_query += " offset %d" % new_start
        if new_stop < self.INF:
            new_query += " limit %d" % max(new_stop - new_start, 0)
        
        ret = EnhancedRawQuerySet(new_query, model=self.model, params=self.params, translations=self.translations, using=self._db)
        if isinstance(k, (int, long)):
            ret = list(ret)[0]
        return ret

    def _fill_cache(self):
        if not hasattr(self, '_result_cache'):
            self._result_cache = list(super(EnhancedRawQuerySet, self).__iter__())

    def __iter__(self):
        self._fill_cache()
        return iter(self._result_cache)

    def __len__(self):
        self._fill_cache()
        return len(self._result_cache)

class FieldChangeDetectorMixin(object):
    DETECT_CHANGE_FIELDS = ()
    def __init__(self, *args, **kw):
        super(FieldChangeDetectorMixin, self).__init__(*args, **kw)
        if self.pk:
            self._prev_values = dict((f, getattr(self, f)) for f in self.DETECT_CHANGE_FIELDS)
        else:
            self._prev_values = {}

    def has_field_changed(self, name):
        if not name in self.DETECT_CHANGE_FIELDS:
            logger.warning("field %r not present in %s.DETECT_CHANGE_FIELDS", name, self.__class__.__name__) 
            return False
        return getattr(self, name, None) != self._prev_values.get(name)

    is_field_changed = has_field_changed

    def any_field_changed(self, *names):
        return any(self.has_field_changed(name) for name in names)

    def prev_value(self, name):
        return self._prev_values.get(name)


class InstanceCache(object):
    @classmethod
    def _create_key(cls, **kw):
        return cache.Key("object", cls.__module__, cls.__name__, kw)

    @classmethod
    def get(cls, **kw):
        key = cls._create_key(**kw)
        obj = cache.get(key)
        if obj is None:
            obj = cls.objects.get(**kw)
            cache.set(key, obj)
        return obj

    def clean_instance_cache(self):
        for kw in self.clean_instance_cache_kwargs():
            key = self._create_key(**kw)
#            logger.debug("clean cache: %r", key, extra={'bg': 'red'})
            cache.delete(key)

    def clean_instance_cache_kwargs(self):
        return dict(id=self.id),

    @classmethod
    def clean_instance_cache_postsave(cls, sender, instance, **kw):
        clean_cache = getattr(instance, 'clean_instance_cache', None)
        if clean_cache:
            clean_cache()

from django.db.models.signals import post_save
post_save.connect(InstanceCache.clean_instance_cache_postsave)

from contextlib import contextmanager

@contextmanager
def transaction():
    from django.db import transaction
    try:
        sid = transaction.savepoint()
        yield
        transaction.savepoint_commit(sid)
    except Exception, e:
        logger.error(unicode(e))
        transaction.savepoint_rollback(sid)

import django.db.models.base
import django.db.models.fields

class ModelBase(django.db.models.base.ModelBase):
    def __new__(meta, name, bases, attrs):
        cls = django.db.models.base.ModelBase.__new__(meta, name, bases, attrs)
        for k, v in attrs.items():
            if isinstance(v, django.db.models.fields.Field) and not hasattr(cls, k):
                if v.default != django.db.models.fields.NOT_PROVIDED:
                    class _getter(object):
                        def __init__(self, default):
                            self.default = default
                        def __get__(self, instance, owner):
                            return (self.default)() if callable(self.default) else self.default
                    setattr(cls, k, _getter(v.default))
        return cls

class Model(django.db.models.Model):
    """
    Base model class providing defaults for missing properties
    """
    
    class Meta:
        abstract = True
    
    __metaclass__ = ModelBase

