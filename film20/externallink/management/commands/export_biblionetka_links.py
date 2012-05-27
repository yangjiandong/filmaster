from django.core.management.base import BaseCommand, CommandError
from django.db import connection

class Command(BaseCommand):
    def handle(self, *args, **options):

        link_query = """
        SELECT o.id, f.title, fl.title, el.url, 'http://filmaster.pl/film/' || o.permalink || '/' as url
        FROM externallink_externallink el
         LEFT JOIN core_film f ON f.parent_id=el.film_id
         LEFT JOIN core_object o ON o.id=f.parent_id
         LEFT JOIN core_objectlocalized ol ON ol.parent_id = o.id AND ol."LANG"='pl'
         LEFT JOIN core_filmlocalized fl ON fl.object_localized_id = ol.id
        WHERE el.url_kind=9 AND el.url LIKE %s
        ORDER BY f.title;"""

        cursor = connection.cursor()

        biblionetka = "http://www.biblionetka.pl/book.aspx"
        q = biblionetka + "%"
        cursor.execute(link_query, (q,) )

        print "<films>"
        for row in cursor.fetchall():
            print "<film>"
            id = row[0]
            title = row[1]
            localized_title = row[2]
            biblionetka = row[3]
            url = row[4]

            print "<id>" + str(id) + "</id>"
            s = "<title><![CDATA[%s]]></title>" % title
            print s.encode('utf-8')
            if localized_title is not None:
                if localized_title != "":
                    s = "<localized-title><![CDATA[%s]]></localized-title>" % localized_title
                    print s.encode('utf-8')
            print "<url>%s</url>" % url
            print "<biblionetka>%s</biblionetka>" % biblionetka
            print "</film>"
        print "</films>"

        cursor.close()
        # http://www.mail-archive.com/django-users@googlegroups.com/msg92582.html
        connection._rollback()
