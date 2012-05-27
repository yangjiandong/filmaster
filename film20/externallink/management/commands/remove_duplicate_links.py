from django.db import connection, transaction
from django.core.management.base import BaseCommand, CommandError

from film20.externallink.models import ExternalLink


class Command(BaseCommand):
    def handle(self, *args, **options):

        query = """SELECT parent_id FROM externallink_externallink
                    WHERE parent_id NOT IN
                        (SELECT MAX( s.parent_id )
                            FROM externallink_externallink as s
                                GROUP BY s."LANG", s.url, s.film_id, s.person_id );
                """

        print "Before: %d, records" % ExternalLink.objects.count()

        cursor = connection.cursor()
        cursor.execute( query )

        for row in cursor.fetchall():
            # remove externallink and all relations ...
            ExternalLink.all_objects.get( pk=row[0] ).delete()

        print "After: %d, records" % ExternalLink.objects.count()
