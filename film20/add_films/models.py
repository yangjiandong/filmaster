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
try:
    from PIL import Image
except ImportError:
    import Image

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _
from django.core.files.images import get_image_dimensions

from film20.utils.slughifi import slughifi
from film20.core.models import Person, Film, Country, Character
from film20.moderation.models import ModeratedObject

try:
    from film20.notification import models as notification
except ImportError:
    notification = None

from film20.add_films.utils import get_film_permalink, get_other_languages


def get_image_path( instance, filename ):
    return "tmp_img/objects/%s/%s" % ( filename[0], filename )

class AddedFilm( ModeratedObject ):
    TYPE_FILM = 1
    TYPE_SERIES = 2
    TYPE_CHOICES = (
        ( TYPE_FILM, _( 'Film' ) ),
        ( TYPE_SERIES, _( 'Tv series' ) ),
    )

    film = models.ForeignKey( Film, blank=True, null=True, verbose_name=_( "Film" ) )

    title = models.CharField( _( "Original Title" ), max_length=128 )
    release_year = models.IntegerField( _( "Release year" ) )

    type = models.IntegerField( _( "Type" ), choices=TYPE_CHOICES, default=TYPE_FILM )
    completion_year = models.IntegerField( _( "Last episode date" ), blank=True, null=True )

    localized_title = models.CharField( _( "Localized Title" ), max_length=128, blank=True, null=True )
    
    directors = models.ManyToManyField( Person, related_name='added_films_directed', blank=True, null=True, verbose_name=_( "Directed by" ) )
    actors = models.ManyToManyField( Person, related_name='added_films_played', blank=True, null=True, through='AddedCharacter', verbose_name=_( "Actors" ) )
    production_country = models.ManyToManyField( Country, related_name='add_films_produced_in', verbose_name=_( "Production Countries" ) )

    image = models.ImageField( _( "Image" ), upload_to=get_image_path, null=True, blank=True )

    user = models.ForeignKey( User, verbose_name=_( "User", related_name = "added_films" ) )
    created_at = models.DateTimeField( _( "Created at" ), auto_now_add=True )

    class Meta:
        ordering = [ "created_at", "user" ]
        verbose_name = _( "Added Film" )
        verbose_name_plural = _( "Added Films" )
        permissions = (
            ( "can_accept_added_films", "Can accept manually added films"),
            # TODO: move from here ?
            ( "can_edit_film_cast", "Can edit film cast"),
        )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.type == self.TYPE_SERIES and not self.completion_year:
            raise ValidationError( _( 'Completion year is required for TV series.' ) )

    def accept( self, user ):
        
        # generate permalink
        permalink = get_film_permalink( self )

        film = Film(
            title = self.title, 
            release_year = self.release_year, 
            image = self.image,
            version = 1,
            is_tv_series = ( self.type == self.TYPE_SERIES ),
            completion_year = self.completion_year if ( self.type == self.TYPE_SERIES ) else None,
            type = Film.TYPE_FILM, 
            permalink = permalink, 
            status = 1,
            production_country_list = ','.join( [ c.country for c in self.production_country.all() ] )
        )
        
        film.save()
        
        # add localized title
        if self.localized_title:
            film.save_localized_title( self.localized_title )

        # add directors
        for director in self.directors.all():
            film.directors.add( director )

            # ... and set director flag to true
            director.is_director = True
            director.save()

        # set countries
        for country in self.production_country.all():
            film.production_country.add( country )
        
        other_languages = get_other_languages()

        # set actors
        for actor in self.get_actors():
            # save charater in default LANG
            Character( 
                film = film, 
                person = actor.person, 
                importance = actor.importance, 
                character = actor.character
            ).save()

            # mark this person as actor
            actor.person.is_actor = True
            actor.save()

            # ... and in other languages
            for lang in other_languages:
                Character( 
                    film = film, 
                    person = actor.person, 
                    importance = actor.importance,
                    LANG=lang
                ).save()

        # set reference
        self.film = film

        super( AddedFilm, self ).accept( user )

    def __unicode__( self ):
        return "%s [%d]" % ( self.title, self.release_year )

    def get_absolute_url( self ):
        if self.moderation_status == AddedFilm.STATUS_ACCEPTED:
            return self.film.get_absolute_url()

        return reverse( "edit-added-film", args=[ self.id ] )
    
    def get_actors( self ):
        return AddedCharacter.objects.filter( added_film = self )

def added_film_post_save( sender, instance, created, *args, **kw ):
    if instance.image:
        d = get_image_dimensions( instance.image )
        if d is None or ( d[0] > 71 or d[1] > 102 ):
            # Ignore all PIL errors, if image is broken 
            #  it just will not be added
            try:
                image = Image.open( instance.image.path )
                image = image.resize( ( 71, 102 ), Image.ANTIALIAS )
                if image.mode != "RGB":
                    image = image.convert( "RGB" )
                image.save( instance.image.path, "JPEG" )
            except IOError:
                pass

    # if moderated send notification ...
    if instance.moderation_status != AddedFilm.STATUS_UNKNOWN \
        and instance.user != instance.moderation_status_by:
        if notification:
            notification.send( [ instance.user ], "added_film_moderated", { "item": instance, 
                                                                            "accepted": instance.moderation_status == AddedFilm.STATUS_ACCEPTED } )

post_save.connect( added_film_post_save, sender=AddedFilm )

class AddedCharacter( models.Model ):
    person = models.ForeignKey( Person, verbose_name=_( "Person" ) )
    added_film = models.ForeignKey( AddedFilm, verbose_name=_( "Film" ) )
    
    importance = models.IntegerField( _( "Importance" ), blank=True, null=True )
    character = models.CharField( _( "Character" ), max_length=255, blank=True, null=True )


from film20.config.urls import urls
from film20.moderation.registry import registry
from film20.moderation.items import ModeratedObjectItem

moderated_added_film = ModeratedObjectItem( 
        AddedFilm, "add_films.can_accept_added_films",
        name=urls["MODERATED_FILMS"], item_template_name="moderation/add_films/record.html",
        rss_template_name="moderation/add_films/rss.xml"
    )

registry.register( moderated_added_film )
