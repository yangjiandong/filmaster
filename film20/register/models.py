from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import User

# Create your models here.
from datetime import datetime

import film20.settings as settings
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", 'en')


class RegistrationModel(models.Model):

    STATUS_CHOICES = (
        (0, 'iPhone'),
        (1, 'Android'),
        (2, 'Windows Mobile'),
        (3, 'Symbian'),
        (4, 'Samsung Bada'),
        (5, 'WebOS'),
        (6, _('Other')),
        (7, _('I don\'t know my platform'))
    )

    user = models.ForeignKey(User, blank=True, null=True) 
    email = models.EmailField(_('Your email address'))
    opinion = models.IntegerField(_('On which platform would you like to run Filmaster Mobile?'), default=7, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=datetime.now)
    beta_code = models.CharField(_('Beta code'), max_length=128, blank=True, null=True)
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    def __unicode__(self):
        return self.email

    class Meta:
        verbose_name = "Registered user"
        verbose_name_plural = "Registered users"

class RegistrationModelAdmin(admin.ModelAdmin):
    list_display        = ('user', 'email', 'opinion', 'beta_code','LANG','created_at')
    raw_id_fields = ['user',]

admin.site.register(RegistrationModel, RegistrationModelAdmin)

