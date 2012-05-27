from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from film20.core.models import Person, Film

class Duplicate( models.Model ):
    user = models.ForeignKey( User, verbose_name=_( "User" ), 
                                    related_name = "%(class)s_requested_duplicate_objects", blank=True, null=True )
    created_at = models.DateTimeField( _( "Created at" ), auto_now_add=True )

    resolved    = models.BooleanField( _( "Resolved" ) )
    resolved_at = models.DateTimeField( _( "Resolved at" ), blank=True, null=True )
    resolved_by = models.ForeignKey( User, verbose_name=_( "Resolved by" ), 
                                    related_name = "%(class)s_duplicate_objects", blank=True, null=True )

    class Meta:
        abstract = True


class DuplicatePerson( Duplicate ):
    personA = models.ForeignKey( Person, related_name="duplicate_person_a", verbose_name=_( "Person" ) )
    personB = models.ForeignKey( Person, related_name="duplicate_person_b", verbose_name=_( "Person" ) )

class DuplicateFilm( Duplicate ):
    filmA = models.ForeignKey( Film, related_name="duplicate_film_a", verbose_name=_( "Film" ) )
    filmB = models.ForeignKey( Film, related_name="duplicate_film_b", verbose_name=_( "Film" ) )
