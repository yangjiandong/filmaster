import os, sys
PROJECT_ROOT = os.curdir
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from django.db import connection

film_query = """
select o.id, f.title, fl.title, 'http://filmaster.pl/film/' || o.permalink || '/' as url from core_film f left join core_object o on o.id=f.parent_id left join core_objectlocalized ol on ol.parent_id = o.id and ol."LANG"='pl' left join core_filmlocalized fl on fl.object_localized_id = ol.id order by f.title"""
    
cursor = connection.cursor()
cursor.execute(film_query)

print "<films>"

for row in cursor.fetchall():
    print "<film>"
    id = row[0]
    title = row[1]
    localized_title = row[2]
    url = row[3]
    
    print "<id>" + str(id) + "</id>"
    s = "<title><![CDATA[%s]]></title>" % title
    print s.encode('utf-8')
    if localized_title is not None:
        if localized_title != "":
            s = "<localized-title><![CDATA[%s]]></localized-title>" % localized_title
            print s.encode('utf-8')
    print "<url> %s </url>" % url
    print "</film>"

print "</films>"

cursor.close()
# http://www.mail-archive.com/django-users@googlegroups.com/msg92582.html
connection._rollback()


