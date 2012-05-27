#!/usr/bin/env python
import os
import psycopg2
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.tagging.models import *

#  delete from tagging_taggeditem where id in( 55501, 55499);
 
tags = Tag.objects.all()
for tag in tags:
    oldname = tag.name
    newname = tag.name.lower()

    if oldname != newname:
	try:
	    identical_tag = Tag.objects.get(name=newname)
	    # if exists, we'll need to rewrite dependant objects
	    print "Identical tag exists: " + unicode(identical_tag)
	    print "Rewriting and removing duplicate tags..." 
	    TaggedItem.objects.filter(tag=tag).update(tag=identical_tag)
	    print "TaggedItems rewritten to " + unicode(newname)
	    tag.delete()
	    print "Tag removed: " + unicode(oldname)
	    
	except Tag.DoesNotExist:
	    # doesn't exist -- ok, updating
	    tag.name = newname
	    print "Updating tag " + unicode(oldname) + " to " + unicode(newname) 
	    tag.save()
