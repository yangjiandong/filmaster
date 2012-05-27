from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.translation import gettext_lazy as _

from film20.core.models import Film
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

# Create your models here.
class FilmToImport(models.Model):
    UNKNOW = -1
    NOT_ACCEPTED = 0
    ACCEPTED = 1
    IMPORT_FAILED = 2
    ALREADY_IN_DB = 3
    TV_SERIES = 4

    IMPORT_STATUS_CHOICES = (
        (NOT_ACCEPTED, _('Not accepted')),
        (ACCEPTED, _('Accepted')),
        (UNKNOW, _('Unknow')),
        (IMPORT_FAILED, _('Import failed')),
        (ALREADY_IN_DB, _('Already in db')),
        (TV_SERIES, _('Tv series WTF?!')),
    )
    
    user = models.ForeignKey(User)
    title = models.CharField(max_length=128)
    imdb_url = models.CharField(blank=True, null=True, max_length=128)
    imdb_id = models.CharField(blank=True, null=True,max_length=10)
    comment = models.TextField(blank=True, null=True)
    is_imported = models.BooleanField(default=False)
    status = models.IntegerField(_('Status'), choices=IMPORT_STATUS_CHOICES, default=UNKNOW)
    created_at = models.DateTimeField(default=datetime.now)
    attempts = models.IntegerField(blank=True, null=True, default=0)
    
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    
    class Meta:
        permissions = (
            ("can_accept_films", "Can accept films to import"),
        )
        verbose_name = _( "Film to import" )
        verbose_name_plural = _( "Films to import" )

    def _set_status( self, status ):
        self.status = status
        self.save()

    def accept( self, user, **kwargs ):
        self._set_status( FilmToImport.ACCEPTED )

    def reject( self, user, reason=None ):
        self._set_status( FilmToImport.NOT_ACCEPTED )


class ImportedFilm(models.Model):
    user = models.ForeignKey(User)
    film = models.ForeignKey(Film)
    created_at = models.DateTimeField(default=datetime.now)


from film20.moderation.registry import registry
from film20.moderation.items import ModeratedItem
from film20.moderation.models import ModeratedObject


class FilmToImportModeratedItem( ModeratedItem ):
    def __init__( self ):

        self.model = FilmToImport
        self.permission = "import_films.can_accept_films"
        self.name = "films-to-import"
        self.item_template_name = "moderation/import_films/record.html"
        self.rss_template_name = "moderation/import_films/rss.xml"

    def get_queryset( self, status ):
        if status == ModeratedObject.STATUS_UNKNOWN:
            status = FilmToImport.UNKNOW

        elif status == ModeratedObject.STATUS_ACCEPTED:
            status = FilmToImport.ACCEPTED

        elif status == ModeratedObject.STATUS_REJECTED:
            status = FilmToImport.NOT_ACCEPTED

        return self.model._default_manager.filter( status=status )

    def accept_item( self, item, user, **kwargs ):
        if self.can_accept( item, user ):
            item.accept( user, **kwargs )
        
        else: raise ModerationException( _( "Permission denied!" ) )

    def reject_item( self, item, user, reason=None ):
        if self.can_reject( item, user ):
            item.reject( user, reason )

        else: raise ModerationException( _( "Permission denied!" ) )

moderated_added_film = FilmToImportModeratedItem()
registry.register( moderated_added_film )
