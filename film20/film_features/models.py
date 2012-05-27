import random
import itertools

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete
from film20.utils import cache

from film20.core.models import Film, Rating, SimilarFilm


TYPE_CHOICES = (
    ( 1 , _( 'Slow pace' ) ),
    ( 2 , _( 'Dynamic' ) ),
    ( 3 , _( 'Serious' ) ),
    ( 4 , _( 'Easy-watching' ) ),
    ( 5 , _( 'Warm' ) ),
    ( 6 , _( 'Depressing' ) ),
    ( 7 , _( 'Touching' ) ),
    ( 8 , _( 'No-brainer' ) ), 
    ( 9 , _( 'Dark' ) ),
    ( 10, _( 'Experimental' ) ),
    ( 11, _( 'Dreamlike' ) ),
    ( 12, _( 'Controversial' ) ),
    ( 13, _( 'Indie' ) ),
    ( 14, _( 'Funny' ) ),
    ( 15, _( 'Challenging' ) ),
    ( 16, _( 'Brutal' ) ),
    ( 17, _( 'Sexually explicit' ) ),
) 

def type_name( type ):
    return [ val for key, val in TYPE_CHOICES if key == type ][0]


class FilmFeatureManager( models.Manager ):

    def is_voted( self, film, user ):
        return FilmFeatureVote.objects.filter( user=user, film=film ).count() > 0

    def next_film_to_vote( self, user, exclude=[], all_movies=False, tag=None ):
        
        voted = [ ff.film.pk for ff in FilmFeatureVote.objects.filter( user=user ) ]
        if all_movies:
            films = Film.objects.all()
        else:
            rated = Rating.get_user_ratings( user )
            films = Film.objects.filter( pk__in=rated )

        if tag:
            films = films.tagged( tag )

        films = films.exclude( pk__in=voted + exclude ).order_by( '?' )
        return films[0] if len( films ) else None


class FilmFeature( models.Model ):
    type = models.IntegerField( _( "type" ), choices=TYPE_CHOICES )
    film = models.ForeignKey( Film, verbose_name=_( "film" ), related_name='features' )
    number_of_votes = models.IntegerField( _( "number of votes" ), default=0 )

    objects = FilmFeatureManager()

    class Meta:
        unique_together = ( 'type', 'film' )
        ordering = [ '-number_of_votes', ]
        verbose_name = _( "Film Feature" )
        verbose_name_plural = _( "Film Features" )

    @property
    def type_name( self ):
        return type_name( self.type )

    @classmethod
    def matching_film_ids(self, include_ids, exclude_ids):
        key = cache.Key("features_film_ids", include_ids, exclude_ids)
        film_ids = cache.get(key)
        if film_ids is None:
            film_ids = Film.objects.filter(features__type__in=include_ids)
            if exclude_ids:
                film_ids = film_ids.exclude(features__type__in=exclude_ids)
            film_ids = set(film_ids.values_list('id', flat=True))
            cache.set(key, film_ids)
        return film_ids

class FilmFeatureVote( models.Model ):
    type = models.IntegerField( _( "type" ), choices=TYPE_CHOICES )
    film = models.ForeignKey( Film, verbose_name=_( "film" ) )
    user = models.ForeignKey( User, verbose_name=_( "user" ) )

    class Meta:
        unique_together = ( 'type', 'film', 'user' )
        verbose_name = _( "Film Feature Vote" )
        verbose_name_plural = _( "Film Feature Votes" )

    @classmethod
    def update_number_of_votes( cls, sender, instance, *args, **kwargs ):
        try:
            votes = cls.objects.filter( film=instance.film, type=instance.type ).count()
            if votes > 0:
                feature, created = FilmFeature.objects.get_or_create( film=instance.film, type=instance.type )
                feature.number_of_votes = votes
                feature.save()
            else:
                FilmFeature.objects.filter( film=instance.film, type=instance.type ).delete()
                
        except FilmFeature.DoesNotExist:
            pass # already removed, ignore

    @property
    def type_name( self ):
        return type_name( self.type )


# connect signals
post_save.connect( FilmFeatureVote.update_number_of_votes, sender=FilmFeatureVote )
post_delete.connect( FilmFeatureVote.update_number_of_votes, sender=FilmFeatureVote )


from django.db.models import Q, Count
class FilmFeatureComparisionVoteManager( models.Manager ):

    def next_to_vote( self, user ):
        items = self.get_query_set().filter( user=user, status=FilmFeatureComparisionVote.STATUS_UNKNOWN )
        if len( items ):
            return items[0]
        
        rated_films = Film.objects.filter( pk__in=Rating.get_user_ratings( user ) )

        similar_films = SimilarFilm.objects.filter( film_a__in=rated_films, film_b__in=rated_films ).values_list( 'film_a', 'film_b' ).order_by( '?' )
        films_with_features = itertools.combinations( set( FilmFeature.objects.filter( film__in=rated_films ).values_list( 'film', flat=True ).order_by( '?' ) ), 2 )
        
        films = [similar_films, films_with_features]
        random.shuffle( films )

        for f in films:
            next_to_rate = self._find_next_to_rate( user, f )
            if next_to_rate:
                return next_to_rate


    def is_voted( self, user, film_a, film_b, feature ):
        return self.get_query_set().filter( Q( film_a=film_a, film_b=film_b ) | Q( film_a=film_b, film_b=film_a ), user=user, feature=feature ).count() == 1

    def store_result( self, user, film_a, film_b, feature, result=None ):
        if result is None:
            status = FilmFeatureComparisionVote.STATUS_SKIPPED
        else:
            status = FilmFeatureComparisionVote.STATUS_VOTED

        qs = self.get_query_set().filter( Q( film_a=film_a, film_b=film_b ) | Q( film_a=film_b, film_b=film_a ), user=user, feature=feature )
        if qs.count() > 0:
            vote = qs[0]
            vote.result=result
            vote.status=status
            vote.save()
        else:
            self.get_query_set().create( user=user,feature=feature, result=result, status=status, film_a=film_a, film_b=film_b )


    def _find_next_to_rate( self, user, similar_films ):
        similar_films = list( similar_films )
        random.shuffle( similar_films )
        for sf in similar_films:
            film_a, film_b = sf
            film_a_types = FilmFeature.objects.filter( film=film_a ).values_list( 'type', flat=True )
            shared_features = list( FilmFeature.objects.filter( film=film_b, type__in=film_a_types ).values_list( 'type', flat=True ) )
            if shared_features:
                random.shuffle( shared_features )
                for f in shared_features:
                    if not self.is_voted( user, film_a, film_b, f ):
                        result = self.get_query_set().create( user=user, feature=f, film_a=Film.objects.get( pk=film_a ), film_b=Film.objects.get( pk=film_b ) )
                        return result


class FilmFeatureComparisionVote( models.Model ):
    STATUS_UNKNOWN = 0
    STATUS_VOTED   = 1
    STATUS_SKIPPED = 2

    STATUS_CHOICES = (
        ( STATUS_UNKNOWN, _( "Unknown" ) ),
        ( STATUS_SKIPPED, _( "Skipped" ) ),
        ( STATUS_VOTED  , _( "Voted" ) ),
    )

    user = models.ForeignKey( User, verbose_name=_( "user" ) )

    feature = models.IntegerField( _( "feature" ), choices=TYPE_CHOICES )
    film_a = models.ForeignKey( Film, verbose_name=_( "film a" ), related_name='film_feature_comparision_a' )
    film_b = models.ForeignKey( Film, verbose_name=_( "film b" ), related_name='film_feature_comparision_b' )
    result = models.ForeignKey( Film, verbose_name=_( "winner" ), related_name='film_feature_comparision_winner', blank=True, null=True )

    date_added = models.DateTimeField( blank=True, null=True, auto_now_add=True )
    status = models.IntegerField( default=STATUS_UNKNOWN, choices=STATUS_CHOICES )

    objects = FilmFeatureComparisionVoteManager()

    class Meta:
        unique_together = ( 'film_a', 'film_b', 'feature', 'user' )

    @property
    def feature_name( self ):
        return type_name( self.feature )

    def __unicode__( self ):
        return "%s, %s (%s)" % ( self.film_a, self.film_b, self.feature_name )

from django.contrib import admin
class FilmFeatureComparisionVoteAdmin( admin.ModelAdmin ):
    raw_id_fields = ( 'film_a', 'film_b', 'result', 'user', )
    list_display = ( 'user', 'film_a', 'film_b', 'date_added', 'result', 'status', )

admin.site.register( FilmFeatureComparisionVote, FilmFeatureComparisionVoteAdmin )
