from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.conf import settings

from film20.core.models import Object
from film20.core.models import Film
from film20.core.models import Person
from film20.core.urlresolvers import make_absolute_url
from film20.config.urls import *
from film20.utils.db import QuerySet, LangQuerySet

from film20.moderation.models import ModeratedObject
try:
    from film20.notification import models as notification
except ImportError:
    notification = None


# Create your models here.
class ExternalLinkQuerySet( LangQuerySet ):
    pass

class ExternalLink( Object, ModeratedObject ):
    REVIEW = 1
    NEWS = 2
    BOOK = 9

    VIDEO = 3
    TRAILER = 4 # DEPRECATED
    FULL_FEATURE = 5
    OTHER_VIDEO = 6
    
    LINK_CHOICES = (
        (REVIEW, _('Review')),
        (NEWS, _('News')),
        (BOOK, _('Book')),
        (VIDEO, _('Video')),
        (TRAILER, _('Trailer')),
        (FULL_FEATURE, _('Full feature')),
        (OTHER_VIDEO, _('Other video')),
    )
    
    objects = ExternalLinkQuerySet.as_manager()
    all_objects = models.Manager()
    parent = models.OneToOneField(Object, parent_link=True)
    title = models.CharField(_('Title'), max_length=200, blank=True)
    url = models.URLField(_('url'), max_length=2048, verify_exists=False)
    url_kind = models.IntegerField(_('url kind'), choices=LINK_CHOICES, default=REVIEW)
    video_thumb = models.CharField(max_length=50, blank=True, null=True)
    excerpt = models.TextField(_('Excerpt'), blank=False, null=True)
    film = models.ForeignKey(Film, related_name="film_link", blank=True, null=True)
    person = models.ForeignKey(Person, related_name="person_link", blank=True, null=True)
    user = models.ForeignKey(User)
    
    created_at = models.DateTimeField(_('Created at'), default=datetime.now)
    updated_at = models.DateTimeField(_('Updated at'))
    
    LANG = models.CharField(max_length=2, default=settings.LANGUAGE_CODE)

    class Meta:
        permissions = (
            ("can_add_link", "Can add link"),
        )
        unique_together = (
            ( 'film', 'url', 'LANG' ), 
            ( 'person', 'url', 'LANG' )
        )
        verbose_name = _( "External link" )
        verbose_name_plural = _( "External links" )

    def unique_error_message( self, model_class, unique_check ):
        if model_class == type( self ) and unique_check == ( 'film', 'url', 'LANG'  ):
            return _( "This film already has the same trailer" )
        return super( ExternalLink, self ).unique_error_message( model_class, unique_check )
      
#    @transaction.commit_on_success    
    def save(self, LANG=settings.LANGUAGE_CODE):
        first_save = False
        if self.pk is None:
            first_save = True
        self.LANG = LANG
        self.updated_at = datetime.now()
        super(ExternalLink, self).save()

        if self.moderation_status == ExternalLink.STATUS_ACCEPTED:
            self.save_activity()

        if self.status == ExternalLink.DELETED_STATUS:
            from film20.threadedcomments.models import ThreadedComment
            ThreadedComment.objects.delete_for_object(self.id)

        self.clear_cache()

    def get_absolute_url(self):
        return make_absolute_url(self.get_slug())

    def get_slug(self):
        return reverse('show_link', args=[unicode(self.user), self.id])

    def get_absolute_url_old_style(self):
        # TODO: http://jira.filmaster.org/browse/FLM-1185
        the_url = settings.FULL_DOMAIN_OLD
        if self.film:
            the_url += "/"+urls["FILM"]+'/'+self.film.permalink +'/' +urls["LINK"]+'-'+unicode(self.id) +"/"
        else:
            the_url += "/"+urls["PERSON"]+'/'+self.person.permalink +'/' +urls["LINK"]+'-'+unicode(self.id) +"/"
        return the_url

    def get_url_kind(self):
        for choice in self.LINK_CHOICES:
            if self.url_kind == choice[0]:
               return choice[1]

    def get_object_url( self ):
        if self.film:
            return self.film.get_absolute_path()
        return reverse( 'show_person', args=( self.person.permalink, ) )

    def get_title(self):
        if self.title:
            return self.title
        else:
            return self.film.get_title() + " - " + self.get_url_kind()

    def get_comment_title(self):
        return self.get_title()

    def clear_cache( self ):
        if self.film:
            from django.core.cache import cache
            from django.utils.http import urlquote
            from django.utils.hashcompat import md5_constructor

            args = md5_constructor(u':'.join([urlquote( var ) for var in [ self.film.pk ] ]))
            cache_key = 'template.cache.%s.%s' % ( 'film_videos', args.hexdigest())
            value = cache.delete( cache_key )

    def get_related_films(self):
        if self.film:
            return self.film,
        return ()

    def save_activity(self):
        """
            Save new activity
        """
        from film20.useractivity.models import UserActivity
        try:
            # Checking if activity already exists for given externallink, if so update activity
            act = UserActivity.objects.get(link=self, user=self.user)
            act.url = self.url
            act.url_kind = self.url_kind
            act.video_thumb = getattr(self, "video_thumb", None)
            act.title = self.get_title()
            act.content = getattr(self, "excerpt", None)
            act.film = getattr(self, "film", None)
            act.film_title = self.film.get_title()
            act.film_permalink = self.film.permalink
            act.status = self.status
            act.permalink = self.get_absolute_url()
            act.save()
        except UserActivity.DoesNotExist:
            # Activity does not exist - create a new one
            act = UserActivity()
            act.user = self.user
            act.username = self.user.username
            act.activity_type = UserActivity.TYPE_LINK
            act.link = self
            act.url = self.url
            act.url_kind = self.url_kind
            act.video_thumb = getattr(self, "video_thumb", None)
            act.title = self.get_title()
            act.content = getattr(self, "excerpt", None)
            act.film = getattr(self, "film", None)
            act.film_title = self.film.get_title()
            act.film_permalink = self.film.permalink
            act.status = self.status
            act.permalink = self.get_absolute_url()
            act.save()


from django.conf import settings

class ExternalLinkToRemoveQuerySet( QuerySet ):
    def default_filter( self ):
        return self.filter( externallink__LANG=settings.LANGUAGE_CODE )


class ExternalLinkToRemove( ModeratedObject ):
    
    user         = models.ForeignKey( User )
    externallink = models.ForeignKey( ExternalLink, related_name="remove_link" )

    class Meta:
       verbose_name = _( "Link to remove" )
       verbose_name_plural = _( "Links to remove" )

    def accept( self, user, **kwargs ):
        super( ExternalLinkToRemove, self ).accept( user, **kwargs )
        
        # send notification and remove externallink
        self.send_notification()
        self.externallink.clear_cache()
        self.externallink.delete()

    def reject( self, user, reason=None ):
        super( ExternalLinkToRemove, self ).reject( user, reason )

        self.send_notification();

    def send_notification( self ):
        if self.user != self.moderation_status_by and notification:
            notification.send( [ self.user ], "link_to_remove_moderated", { "item": self } )


# register moderated items

from film20.moderation.registry import registry
from film20.moderation.items import ModeratedObjectItem

moderated_links = ModeratedObjectItem( 
        ExternalLink, "externallink.can_add_link",
        name="externallink", 
        item_template_name="moderation/externallink/record.html",
        rss_template_name="moderation/externallink/rss.xml"
    )

moderated_links_to_remove = ModeratedObjectItem( 
        ExternalLinkToRemove, "externallink.can_add_link",
        name="externallink-tr", 
        item_template_name="moderation/externallink-tr/record.html",
        rss_template_name="moderation/externallink-tr/rss.xml"
    )

registry.register( moderated_links )
registry.register( moderated_links_to_remove )
