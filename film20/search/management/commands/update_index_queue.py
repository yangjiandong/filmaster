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

from optparse import make_option

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from film20.core.management.base import BaseCommand

from haystack import site
from haystack.exceptions import NotRegistered

from film20.search.models import QueuedItem


DEFAULT_BATCH_SIZE = getattr( settings, 'HAYSTACK_BATCH_SIZE', 1000 )

class Command( BaseCommand ):
    help = "Freshens the search index queue."

    option_list = BaseCommand.option_list + (
        make_option( '-b', '--batch-size', action='store', dest='batchsize',
                    default=DEFAULT_BATCH_SIZE, type='int',
                    help='Number of items to index at once.'
        ),
    )

    def handle( self, **options ):
        self.verbosity = int( options.get( 'verbosity', 1 ) )
        self.batchsize = options.get( 'batchsize', DEFAULT_BATCH_SIZE )

        for model, index in site.get_indexes().items():
            self.update_by_model( model, index )

    def update_by_model( self, model, index ):
        content_type = ContentType.objects.get_for_model( model )
        
        if self.verbosity > 0:
            print " >> %s.%s" % ( model._meta.app_label, model._meta.module_name )
        
        # 1. update indexes 
        qs = QueuedItem.objects.get_for_language().filter( content_type = content_type, 
                                       action_type = QueuedItem.ACTION_UPDATED )
        total = qs.count()

        if total > 0 and self.verbosity > 0:
            print "   -- %d to add." % total

        for start in range( 0, total, self.batchsize ):
            end = min( start + self.batchsize, total )
            
            small_cache_qs = qs.all()

            queued_qs = small_cache_qs[start:end]
            to_update = []
            for item in queued_qs:
                if item.content_object is None:
                    item.delete()
                else:
                    to_update.append( item )


            current_qs = [ obj.content_object for obj in to_update ]

            if self.verbosity > 1:
                print "  indexing %s - %d of %d." % ( start + 1, end, total )

            try:
                index.backend.update( index, current_qs )
                for obj in queued_qs:
                    obj.delete()

            except Exception, e:
                print "  update error:", e

        # 1. remove indexes 
        qs = QueuedItem.objects.get_for_language().filter( content_type = content_type, 
                                       action_type = QueuedItem.ACTION_REMOVED )
        total = qs.count()

        if total > 0 and self.verbosity > 0:
            print "   -- %d to remove." % total
        
        for item in qs:
            try:
                index.backend.remove( "%s.%s.%d" % ( item.content_type.app_label, 
                                                    item.content_type.model_class()._meta.module_name, item.object_id ) )
                item.delete()

            except Exception, e:
                print "  remove error:", e


