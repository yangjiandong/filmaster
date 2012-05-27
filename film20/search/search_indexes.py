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
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from haystack import site, backend
from haystack.indexes import *
from haystack.query import SearchQuerySet
from haystack.backends import SQ, SearchBackend

from film20.search.models import QueuedItem
from film20.search.utils import get_available_languages

from film20.blog.models import Post
from film20.utils.texts import normalized_text
from film20.threadedcomments.models import ThreadedComment
from film20.core.models import Film, Object, Person, ShortReview, FilmLocalized, PersonLocalized

from film20.search.solr_helper import is_supported, is_testing_mode

class QueueSearchIndex( RealTimeSearchIndex ):

    def is_testing_mode( self ):
        if not hasattr( self, '__test_mode'):
            self.__test_mode = is_supported() and is_testing_mode()
        return self.__test_mode

    def _setup_save( self, model ):
        signals.post_save.connect( self.pre_queue_update, sender=model)

    def _setup_delete( self, model ):
        signals.post_delete.connect( self.pre_queue_remove, sender=model)

    def _teardown_save( self, model ):
        signals.post_save.disconnect( self.pre_queue_update, sender=model )

    def _teardown_delete( self, model ):
        signals.post_delete.disconnect( self.pre_queue_remove, sender=model )

    def _propagate_to_all_languages( self, obj, status ):
        if self.is_testing_mode():
            return self.remove_object( obj ) if status == QueuedItem.ACTION_REMOVED else self.update_object( obj )

        for language in get_available_languages():
            QueuedItem.objects.add_to_queue( obj, status, language )
    
    def _get_module_name( self, instance ):
        return "%s_%s" % ( instance._meta.app_label, instance._meta.module_name )

    def _get_method( self, method_name ):
        if hasattr( self, method_name ):
            return getattr( self, method_name )
        else:
            return None

    def pre_queue_remove( self, instance, **kwargs ):
        method = self._get_method( "pre_rm_%s" % self._get_module_name( instance ) )
        if method: method( instance )
        else:
            self.queue_to_remove( instance )

    def pre_queue_update( self, instance, **kwargs ):
        method = self._get_method( "pre_upd_%s" % self._get_module_name( instance ) )
        if method: method( instance )
        else:
            self.queue_to_update( instance )

    def queue_to_update( self, obj ):
        if self.is_testing_mode():
            return self.update_object( obj )
        QueuedItem.objects.add_to_queue( obj, QueuedItem.ACTION_UPDATED )

    def queue_to_remove( self, obj ):
        if self.is_testing_mode():
            return self.remove_object( obj )
        QueuedItem.objects.add_to_queue( obj, QueuedItem.ACTION_REMOVED )

    def pre_upd_blog_post( self, obj ):
        # update only if is public 
        #    in other case object should be removed from index
        self.queue_to_update( obj ) if obj.is_public \
            else self.queue_to_remove( obj )

    def pre_upd_core_film( self, obj ):
        self._propagate_to_all_languages( obj, QueuedItem.ACTION_UPDATED )

    def pre_rm_core_film( self, obj ):
        self._propagate_to_all_languages( obj, QueuedItem.ACTION_REMOVED )

    def pre_upd_core_person( self, obj ):
        self._propagate_to_all_languages( obj, QueuedItem.ACTION_UPDATED )

    def pre_rm_core_person( self, obj ):
        self._propagate_to_all_languages( obj, QueuedItem.ACTION_REMOVED )

class FilmIndex( QueueSearchIndex ):
    title = CharField( model_attr='title', weight=0.9 )
    text = CharField( document=True, use_template=True, weight=0.6 )
    # ..
    popularity = FloatField( model_attr='popularity' )

    order = 0
    short_name = 'film'

    def prepare( self, obj ):
        data = super( FilmIndex, self ).prepare( obj )
        data['boost'] = self.prepare_popularity( obj ) * 0.1
        return data

    def prepare_popularity( self, obj ):
        return float( obj.popularity )

    def prepare_title( self, obj ):
        result = []
        # 1. add film.title
        result.append( obj.title )
        if obj.title_normalized not in result:
            result.append( obj.title_normalized )

        # 2. add title in current locale
        try:
            film = FilmLocalized.objects.get( film=obj, LANG=settings.LANGUAGE_CODE )
            if not film.title in result:
                result.append( film.title )
            if not film.title_normalized in result:
                result.append( film.title_normalized )
        except FilmLocalized.DoesNotExist: pass
        except Exception, e: 
            print "Exception on film localized: ", e
        
        # 3. add english title
        try:
            film = FilmLocalized.objects.get( film=obj, LANG='en' )
            if not film.title in result:
                result.append( film.title )
            if not film.title_normalized in result:
                result.append( film.title_normalized )
        except FilmLocalized.DoesNotExist: pass
        except Exception, e: 
            print "Exception on film localized: ", e
        
        return " ".join( result )

    def index_queryset( self ):
        return Film.objects.distinct().select_related()

class PersonIndex( QueueSearchIndex ):
    title = CharField( model_attr='name', weight=0.9 )
    text = CharField( document=True, use_template=True, weight=0.6 )
    popularity = FloatField( model_attr='actor_popularity' )
    
    # ..
    surname = CharField( model_attr='surname', weight=1.0 )
    firstname = CharField( model_attr='name', weight=0.8 )

    order = 1
    short_name = 'person'

    def prepare( self, obj ):
        data = super( PersonIndex, self ).prepare( obj )
        data['boost'] = self.prepare_popularity( obj ) * 0.1
        return data

    def prepare_title( self, obj ):
        result = []

        # 1. add actor
        full_name = "%s %s" % ( obj.name, obj.surname )
        result.append( full_name )
        
        # ... and normalized
        normalized = normalized_text( full_name )
        if normalized and not normalized in result:
            result.append( normalized )

        # 2. add actor in current locale
        try:
            person = PersonLocalized.objects.get( person=obj, LANG=settings.LANGUAGE_CODE )
            full_name = "%s %s" % ( person.name, person.surname )
            if not full_name in result:
                result.append( full_name )

            # ... and normalized
            normalized = normalized_text( full_name )
            if normalized and not normalized in result:
                result.append( normalized )

        except PersonLocalized.DoesNotExist: pass
        except Exception, e: 
            print "Exception on person localized: ", e

        return " ".join( result )

    def prepare_popularity( self, obj ):
        return float( obj.actor_popularity + obj.director_popularity + obj.writer_popularity )

    def index_queryset( self ):
        return Person.objects.all()

class UserIndex( QueueSearchIndex ):
    title = CharField( model_attr='username', weight=0.9 )
    text = CharField( document=True, use_template=True, weight=0.6 )

    order = 2
    short_name='user'

    def index_queryset( self ):
        return User.objects.all()

class PostIndex( QueueSearchIndex ):
    title = CharField( model_attr='title', weight=0.9 )
    text = CharField( document=True, use_template=True, weight=0.6 )

    order = 3
    short_name = 'post'

    def index_queryset( self ):
        return Post.objects.filter( is_public=True )

class ShortReviewIndex( QueueSearchIndex ):
    text = CharField( document=True, use_template=True, weight=0.6 )

    order = 4
    short_name = 'review'

    def index_queryset( self ):
        return ShortReview.objects.all()

class CommentIndex( QueueSearchIndex ):
    text = CharField( document=True, use_template=True, weight=0.6 )

    order = 5
    short_name = 'comment'

    def index_queryset( self ):
        # exclude deprecated forum comments
        forum_type = ContentType.objects.get( app_label="forum", model="thread" )
        return ThreadedComment.objects.filter( ~Q( content_type = forum_type ), is_public=True )

class FakeIndex( QueueSearchIndex ):
    def __init__( self ):
        self.backend = backend.SearchBackend()

# update index queue after localized film edit
fake_index = FakeIndex()
def post_film_localized_save( sender, instance, **kwargs ):
    fake_index.pre_queue_update( instance.film )

# ... and person also
def post_person_localized_save( sender, instance, **kwargs ):
    fake_index.pre_queue_update( instance.person )

signals.post_save.connect( post_film_localized_save, sender=FilmLocalized )
signals.post_save.connect( post_person_localized_save, sender=PersonLocalized )

site.register( Film, FilmIndex )
site.register( Person, PersonIndex )
site.register( User, UserIndex )
site.register( Post, PostIndex )
site.register( ShortReview, ShortReviewIndex )
site.register( ThreadedComment, CommentIndex )
