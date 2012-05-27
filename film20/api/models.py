from django.db import models

class SaaSUser(models.Model):
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=64)
    
    user_prefix = models.CharField(max_length=8)

    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.username
    
    def check_password(self, password):
        # TODO - add password hashing
        return self.password == password
