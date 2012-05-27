from UserDict import UserDict
class _NoPickleDict(UserDict):
    """
    dict subclass which pickles empty
    """
    def __getstate__(self):
        return self.__class__().__dict__

def memoize_method(method):
    """Memoizes expensive method call result (cached in instance)"""
    def wrapper(self, *args, **kw):
        key = method.__name__, args, tuple(kw.items())
        if not hasattr(self, '__memoize_cache'):
            self.__memoize_cache = _NoPickleDict()
        if key in self.__memoize_cache:
            return self.__memoize_cache[key]
        ret = self.__memoize_cache[key] = method(self, *args, **kw)
        return ret
    return wrapper
