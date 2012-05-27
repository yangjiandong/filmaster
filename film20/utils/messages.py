from django.contrib.messages.storage.cookie import CookieStorage as Storage
import logging
logger = logging.getLogger(__name__)

class CookieUniqueStorage(Storage):
    def __iter__(self):
        iter = super(CookieUniqueStorage, self).__iter__()
        seen = set()
        for i in iter:
            if not unicode(i) in seen:
                yield i
                seen.add(unicode(i))

