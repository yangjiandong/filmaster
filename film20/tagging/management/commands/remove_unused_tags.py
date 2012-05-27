from django.db import connection, transaction
from film20.core.management.base import BaseCommand, CommandError

from film20.tagging.models import Tag

class Command( BaseCommand ):
    help = "Removes unused tags."

    def handle( self, **options ):
        self.verbosity = int( options.get( 'verbosity', 1 ) )
        
        query = """
            SELECT
                tagging_tag.id,
                tagging_tag.name, 
                tagging_tag."LANG", 
                COUNT( tagging_taggeditem.id ) AS count
            FROM 
                tagging_tag 
            LEFT join tagging_taggeditem 
                ON tagging_tag.id = tagging_taggeditem.tag_id 

            GROUP BY tagging_tag.id, tagging_tag.name, tagging_tag."LANG"
            HAVING COUNT( tagging_taggeditem.id ) = 0
            ORDER BY count DESC
        """


        if self.verbosity > 1:
            print "Before: %d, records" % Tag.all_objects.count()

        cursor = connection.cursor()
        cursor.execute( query )

        for row in cursor.fetchall():
            id = row[0]
            name = row[1]
            count = row[2]
            
            if self.verbosity > 1:
                print " -- removing tag: ", name
            
            Tag.all_objects.get( pk=id ).delete()

        if self.verbosity > 1:
            print "After: %d, records" % Tag.all_objects.count()
