from .cache import *

def cache_query(query, prefix, *args):
    key = Key(prefix, *args)
    result = get(key)
    if result is None:
        result = list(query)
        set(key, result)
    return result
