from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from film20.tagging.models import Tag, TaggedItem

class Command( BaseCommand ):
    help = "Duplicates all the tags that are assigned to Polish and English LANG."

    def handle( self, **options ):
        self.verbosity = int( options.get( 'verbosity', 1 ) )

        if self.verbosity > 1:
            print "Before: %d, records" % Tag.all_objects.count()

        for ti in TaggedItem.all_objects.all():
            if self.verbosity > 1:
                print " -- tagged item %s, %s" % ( ti.tag.name, ti.tag.LANG )

            if ti.object and hasattr( ti.object, 'LANG' ):
                if ti.object.LANG != ti.tag.LANG:
                    if self.verbosity > 1:
                        print "  `-- TaggedItem.object.LANG(%s) != tag.LANG(%s)" % ( ti.object.LANG, ti.tag.LANG )

                    tag, created = Tag.all_objects.get_or_create( name=ti.tag.name, LANG=ti.object.LANG )
                    try:
                        TaggedItem.all_objects.get( tag=tag, content_type=ti.content_type, object_id=ti.object_id )
                        print " +++ Tag %s already assigned to object %s [REMOVING]" % ( tag, ti.object )
                        ti.delete()
                    except TaggedItem.DoesNotExist:
                        ti.tag = tag
                        ti.save()

                elif self.verbosity > 1:
                    print "  `-- TaggedItem.object.LANG(%s) == tag.LANG(%s) [OK]" % ( ti.object.LANG, ti.tag.LANG )

            else:
                print " TaggedItem.object doesnt have LANG property ... [SKIPPING]"


        call_command( 'remove_unused_tags' )
        
        if self.verbosity > 1:
            print "After: %d, records" % Tag.all_objects.count()
