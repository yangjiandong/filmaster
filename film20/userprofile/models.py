#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# coding=UTF-8
from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.template import loader, Context
from django.core.mail import send_mail
from django.conf import settings
from film20.userprofile.countries import CountryField
from film20.core.urlresolvers import reverse
import datetime
import cPickle as pickle
import base64
try:
    from PIL import Image, ImageFilter
except:
    import Image, ImageFilter
import os.path
import urllib2
AVATAR_SIZES = settings.AVATAR_SIZES

from film20.utils import cache_helper as cache

import logging
logger = logging.getLogger(__name__)

class BaseProfile(models.Model):
    """
    User profile model
    """

    user = models.ForeignKey(User, unique=True)
    display_name = models.CharField(_('Display name'), max_length=30, unique=True, null=True)
    date = models.DateTimeField(default=datetime.datetime.now)
    country = CountryField(_('Country'),null=True, blank=True)
    latitude = models.DecimalField(_('Latitude'), max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(_('Longitude'), max_digits=10, decimal_places=6, blank=True, null=True)
    location = models.CharField(_('Location'), max_length=255, blank=True)
 
    custom_dashboard_filter = models.BooleanField( _( "Custom dashboard filter" ), default=False )   
    activities_on_dashboard = models.CommaSeparatedIntegerField( _( "Activities on dashboard" ), max_length=255, blank=True, null=True )

    class Meta:
        abstract = True

    def has_avatar(self):
        #who is using count to chec if something exist?!
        #return Avatar.objects.filter(user=self.user, valid=True).count()
        try:
            avatar = Avatar.objects.get(user=self.user, valid=True)
            return True
        except Avatar.DoesNotExist:
            return False

    def __unicode__(self):
        return _("%s's profile") % self.user

    def get_absolute_url(self):
        return reverse("profile_public", args=[self.user])


class Avatar(models.Model):
    """
    Avatar model
    """
    image = models.ImageField(upload_to="avatars/%Y/%b/%d")
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    valid = models.BooleanField()

    class Meta:
        unique_together = (('user', 'valid'),)

    def __unicode__(self):
        return _("%s's Avatar") % self.user

    def delete(self):
        base, filename = os.path.split(self.image.path)
        name, extension = os.path.splitext(filename)
        for key in AVATAR_SIZES:
            try:
                os.remove(os.path.join(base, "%s.%s%s" % (name, key, extension)))
            except Exception,e:
                logger.debug("Fatal exception occurred when deleting avatar!")
                logger.debug(e)

        self.clear_cache();

        super(Avatar, self).delete()

    def save(self):
        avatars = Avatar.objects.filter(user=self.user, valid=self.valid).exclude(id=self.id)
        if not avatars:
            self.clear_cache()

        for avatar in avatars:
            base, filename = os.path.split(avatar.image.path)
            name, extension = os.path.splitext(filename)
            avatar.delete()

        super(Avatar, self).save()
        
        # generate all thumbnails
        from film20.utils.avatars import get_avatar_path
        for size in AVATAR_SIZES:
            get_avatar_path(self.user, size)

    def get_thumbnail_path(self, size):
        DEFAULT_AVATAR = getattr(settings, "DEFAULT_AVATAR", os.path.join(settings.MEDIA_ROOT, "img/avatars/generic.jpg"))
        avatar_path = unicode(self.image) or DEFAULT_AVATAR
        path, ext = os.path.splitext(avatar_path)
        return "%s.%s%s" % (path, size, ext)

    def clear_cache( self ):
        for size in AVATAR_SIZES:
            key = cache.Key( "avatar", str(self.user), str(size) )
            cache.delete( key )

    @classmethod
    def create_from_url(cls, user, picture_url):
        dir = datetime.date.today().strftime("avatars/%Y/%b/%d")
        path = settings.MEDIA_ROOT + dir
        if not os.path.isdir(path):
              os.makedirs(path)
        image = '%s/%s.jpg' %  (path, str(user.username))
        img = urllib2.urlopen(picture_url).read()
        tmp = open('%s/%s.jpg' %  (path, str(user.username)), 'wb')
        tmp.write(img)
        tmp.close()
        i = Image.open(image)
        i.thumbnail((480, 480), Image.ANTIALIAS)
        i.convert("RGB").save(image, "JPEG")
        image = '%s/%s.jpg' %  (dir, user.username)
        avatar = cls(user=user, image=image, valid=True)
        avatar.save()

class EmailValidationManager(models.Manager):
    """
    Email validation manager
    """
    def verify(self, key):
        try:
            verify = self.get(key=key)
            if not verify.is_expired():
                verify.user.email = verify.email
                verify.user.save()
                verify.delete()
                return True
            else:
                verify.delete()
                return False
        except:
            return False

    def getuser(self, key):
        try:
            return self.get(key=key).user
        except:
            return False

    def add(self, user, email):
        """
        Add a new validation process entry
        """
        while True:
            key = User.objects.make_random_password(70)
            try:
                EmailValidation.objects.get(key=key)
            except EmailValidation.DoesNotExist:
                self.key = key
                break

        template_body = "userprofile/email/validation.txt"
        template_subject = "userprofile/email/validation_subject.txt"
        site_name, domain = Site.objects.get_current().name, Site.objects.get_current().domain
        body = loader.get_template(template_body).render(Context(locals()))
        subject = loader.get_template(template_subject).render(Context(locals())).strip()
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[email])
        user = User.objects.get(username=str(user))
        self.filter(user=user).delete()
        return self.create(user=user, key=key, email=email)

class EmailValidation(models.Model):
    """
    Email Validation model
    """
    user = models.ForeignKey(User, unique=True)
    email = models.EmailField(blank=True)
    key = models.CharField(max_length=70, unique=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    objects = EmailValidationManager()

    def __unicode__(self):
        return _("Email validation process for %(user)s") % { 'user': self.user }

    def is_expired(self):
        return (datetime.datetime.today() - self.created).days > 0

    def resend(self):
        """
        Resend validation email
        """
        template_body = "userprofile/email/validation.txt"
        template_subject = "userprofile/email/validation_subject.txt"
        site_name, domain = Site.objects.get_current().name, Site.objects.get_current().domain
        key = self.key
        body = loader.get_template(template_body).render(Context(locals()))
        subject = loader.get_template(template_subject).render(Context(locals())).strip()
        send_mail(subject=subject, message=body, from_email=None, recipient_list=[self.email])
        self.created = datetime.datetime.now()
        self.save()
        return True

