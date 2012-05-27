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
from datetime import datetime, timedelta
from random import random
from hashlib import sha1
import urllib
from django.contrib import admin

from django.db import models, IntegrityError, connection
from django.template.loader import render_to_string
from film20.core.urlresolvers import reverse as our_reverse
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives

from django.conf import settings

from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)

# this code based in-part on django-registration

class EmailAddressManager(models.Manager):
    
    def add_email(self, user, email, email_registration=False):
        try:
            email_address = self.create(user=user, email=email)
            if not email_registration:
                EmailConfirmation.objects.send_confirmation(email_address)
            else:
                EmailConfirmation.objects.email_registration(email_address)
            return email_address
        except IntegrityError:
            # Required to clear PostgreSQL's failed transaction
            # See http://jira.filmaster.org/browse/FLM-761
            logger.debug("IntegrityError occured - closing connection!")
            connection.close()
            return None

    def get_primary(self, user):
        try:
            return self.get(user=user, primary=True)
        except EmailAddress.DoesNotExist:
            return None
    
    def get_users_for(self, email):
        """
        returns a list of users with the given email.
        """
        # this is a list rather than a generator because we probably want to do a len() on it right away
        return [address.user for address in EmailAddress.objects.filter(verified=True, email=email)]
    

class EmailAddress(models.Model):
    
    user = models.ForeignKey(User)
    email = models.EmailField( unique=True )
    verified = models.BooleanField(default=False)
    primary = models.BooleanField(default=False)
    
    objects = EmailAddressManager()
    
    def set_as_primary(self, conditional=False):
        old_primary = EmailAddress.objects.get_primary(self.user)
        if old_primary:
            if conditional:
                return False
            old_primary.primary = False
            old_primary.save()
        self.primary = True
        self.save()
        self.user.email = self.email
        self.user.save()
        return True
    
    def __unicode__(self):
        return u"%s (%s)" % (self.email, self.user)
    
    class Meta:
        unique_together = (
            ("user", "email"),
        )

class EmailAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'email', 'verified', )
    search_fields = ('email','user__username')
    raw_id_fields = ['user', ]

class EmailConfirmationManager(models.Manager):
    
    def confirm_email(self, confirmation_key):
        try:
            confirmation = self.get(confirmation_key=confirmation_key)
        except self.model.DoesNotExist:
            return None
        if not confirmation.key_expired():
            email_address = confirmation.email_address
            email_address.verified = True
            email_address.set_as_primary(conditional=True)
            email_address.save()
            return email_address
    
    def send_confirmation(self, email_address):
        salt = sha1(str(random())).hexdigest()[:5]
        confirmation_key = sha1(salt + email_address.email).hexdigest()
        activate_url = our_reverse(
                "film20.emailconfirmation.views.confirm_email",
                args=(confirmation_key,)
        )
        
        subject = render_to_string("emailconfirmation/email_confirmation_subject.txt")
        # strip newline signs
        subject = subject.rstrip('\n')
        # the above line added by Borys Musielak to eliminate "Header values can't contain newlines" exceptions 
        message = render_to_string("emailconfirmation/email_confirmation_message.txt", {
            "user": email_address.user,
            "activate_url": activate_url,
        })
        message_html = render_to_string("emailconfirmation/email_confirmation_message.html", {
            "user": email_address.user,
            "activate_url": activate_url,
        })
        msg = EmailMultiAlternatives(
                subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [email_address.email]
        )
        msg.attach_alternative(message_html, "text/html")
        # msg.content_subtype = "html"
        msg.send()
        
        return self.create(email_address=email_address, sent=datetime.now(), confirmation_key=confirmation_key)
    
    def email_registration(self, email_address):
        salt = sha1(str(random())).hexdigest()[:5]
        confirmation_key = sha1(salt + email_address.email).hexdigest()
        tmp_user = email_address.user.username
        register_url = our_reverse("acct_signup") + '?' + urllib.urlencode((
            ('confirmation_key', confirmation_key),
            ('tmp_user', tmp_user),
        ))
        
        subject = render_to_string("emailconfirmation/email_registration_subject.txt")
        # strip newline signs
        subject = subject.rstrip('\n')
        # the above line added by Borys Musielak to eliminate "Header values can't contain newlines" exceptions 
        message = render_to_string("emailconfirmation/email_registration_message.txt", {
            "user": email_address.user,
            "register_url": register_url,
        })
        message_html = render_to_string("emailconfirmation/email_registration_message.html", {
            "user": email_address.user,
            "register_url": register_url,
        })
        msg = EmailMultiAlternatives(
                subject, 
                message, 
                settings.DEFAULT_FROM_EMAIL, 
                [email_address.email]
        )
        msg.attach_alternative(message_html, "text/html")
        # msg.content_subtype = "html"
        msg.send()
        return self.create(email_address=email_address, sent=datetime.now(), confirmation_key=confirmation_key)
    
    def delete_expired_confirmations(self):
        for confirmation in self.all():
            if confirmation.key_expired():
                confirmation.delete()

class EmailConfirmation(models.Model):
    
    email_address = models.ForeignKey(EmailAddress)
    sent = models.DateTimeField()
    confirmation_key = models.CharField(max_length=40)
    
    objects = EmailConfirmationManager()
    
    def key_expired(self):
        expiration_date = self.sent + timedelta(days=settings.EMAIL_CONFIRMATION_DAYS)
        return expiration_date <= datetime.now()
    key_expired.boolean = True
    
    def __unicode__(self):
        return u"confirmation for %s" % self.email_address

class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ('email_address', 'sent', 'confirmation_key', )
    search_fields = ('email_address__email', )
