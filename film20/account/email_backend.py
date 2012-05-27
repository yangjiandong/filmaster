from django.contrib.auth.backends import ModelBackend
try:
  from django.forms.fields import email_re
except ImportError, e:
  # django 1.2
  from django.core.validators import email_re
  
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models import signals
from django.conf import settings
from film20.utils import cache

class CachedModelBackend(ModelBackend):
    def get_user(self, user_id):
        key = cache.Key("user", user_id)
        user = settings.CACHED_USERS and cache.get(key) or None
        if not user:
            try:
                user = super(CachedModelBackend, self).get_user(user_id)
                if settings.CACHED_USERS:
                    cache.set(key, user)
            except User.DoesNotExist, e:
                pass
        return user or None
    
    @classmethod
    def update_cache(cls, sender, instance, *args, **kw):
        cache.set(cache.Key("user", instance.pk), instance)

signals.post_save.connect(CachedModelBackend.update_cache, sender=User)

class EmailLoginBackend(CachedModelBackend):
    def authenticate(self, username=None, password=None):
        if email_re.search(username):
            try:
                user = User.objs.get(email__iexact=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        return None

class CaseInsensitiveLoginBackend(CachedModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objs.get(username__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        return None
