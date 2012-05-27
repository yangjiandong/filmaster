from django.contrib.auth.models import User
from models import *

class OAuthBackend(object):
    def authenticate(self, service=None, user_id=None):
        try:
            return service.get_user(user_id)
        except User.DoesNotExist, e:
            return None
        
    def get_user(self, id):
        try:
            return User.objects.get(pk=id)
        except User.DoesNotExist, e:
            return None

class TwitterAuthBackend(OAuthBackend):
    service_class = TwitterService

class FourSquareAuthBackend(OAuthBackend):
    service_class = FourSquareService
