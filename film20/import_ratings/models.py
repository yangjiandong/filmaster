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
# Python
import re
from datetime import datetime

# Django
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import simplejson as json

# Project
from film20.notification.models import send as send_notice
from film20.core.deferred import defer

def save_ratings_in_db(user, ratings, kind, overwrite=False):
    films = json.dumps(ratings)
    ImportRatings.objects.create(movies=films, user=user, overwrite=overwrite, kind=kind)

# Create your models here.
class ImportRatings(models.Model):
    
    IMDB = 1
    CRITICKER = 2
    FILMWEB = 3
    
    IMPORT_CHOICES = (
        (IMDB, 'imdb'),
        (CRITICKER, 'criticker'),
        (FILMWEB, 'filmweb'),
    )

    STATUS_UNKNOWN = 0
    STATUS_IMPORT_FAILED = 2
    STATUS_IMPORT_SUCCESSFUL = 3

    IMPORT_STATUS_CHOICES = (
        ( STATUS_UNKNOWN, _( 'Unknown' ) ),
        ( STATUS_IMPORT_FAILED, _( 'Import failed' ) ),
        # ...
        # ...
    )

    user = models.ForeignKey(User)
    overwrite = models.BooleanField(_('Overwrite existing'), db_column='overwrite_rating', default=False)
#    import_reviews = models.BooleanField(_('Import reviews'), null=True, default=False)
#    score_convertion = models.CharField(_('Score convertion'), null=True, default=SCORE_AUTO)
    kind = models.IntegerField(_('Kind'), choices=IMPORT_CHOICES)
    submited_at = models.DateTimeField(_('Submited at'), default=datetime.now)
    imported_at = models.DateTimeField(_('Imported at'), null=True, blank=True)
    movies = models.TextField(_('Rated movies'), null=True, blank=True)
    is_imported = models.BooleanField(_('Is imported'), default=False)

    attempts = models.IntegerField( _( "Number of attemts" ), default=0 )
    import_status = models.IntegerField( _( 'Status' ), choices=IMPORT_STATUS_CHOICES, default=STATUS_UNKNOWN )
    import_error_message = models.TextField( blank=True, null=True )

    def send_import_failed_notification( self ):
        send_notice( [self.user], "import_ratings_failed", {} )
       
    @classmethod
    def post_save(cls, sender, instance, *args, **kw):
        from film20.import_ratings.import_ratings_helper import import_ratings
        defer(import_ratings)

models.signals.post_save.connect(ImportRatings.post_save, sender=ImportRatings)

class ImportRatingsLog(models.Model):
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(_('Created at'), default=datetime.now)
    
    movies_rated = models.TextField(_('Rated movies'), null=True, blank=True)
    movies_already_rated = models.TextField(_('Already rated movies'), null=True, blank=True)
    movies_not_rated = models.TextField(_('Not rated movies'), null=True, blank=True)

    def __str__(self):
        str = "Import for user: %s " % self.user.username
        return str

def send_notification(sender, instance, created, *args, **kw):
    data = {
        'summary_id': instance.id,
    }
    send_notice([instance.user], "import_ratings_log", data)
models.signals.post_save.connect(send_notification, sender=ImportRatingsLog)
