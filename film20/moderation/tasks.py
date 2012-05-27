from celery.task import task
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from film20.core.models import ObjectLocalized
from film20.tagging.models import Tag, TaggedItem
from film20.notification import models as notification

@task
@transaction.commit_manually
def rename_tag( tag_a, tag_b, user ):

    ctx = {
        'success': False,
        'title'  : _( "Renaming tag %(tag_a)s to %(tag_b)s" ) % { 'tag_a': tag_a, 'tag_b': tag_b }
    }

    try:
        tag_a = Tag.objects.get( name=tag_a )
        tag_b, created = Tag.objects.get_or_create( name=tag_b )

        # replace tags
        for obj in TaggedItem.objects.filter( tag=tag_a ):
            # if objects is already tagged with tag 'a' 
            #   we must remove this relation
            try:
                ti = TaggedItem.objects.get( tag=tag_b, content_type=obj.content_type, object_id=obj.object_id )
                ti.delete()

            except TaggedItem.DoesNotExist:
                pass

            obj.tag = tag_b
            obj.save()
            
            # update object localized tag_list
            if isinstance( obj.object, ObjectLocalized ):
                obj.object.tag_list = ', '.join( [ tag.name for tag in Tag.objects.get_for_object( obj.object ) ] )
                obj.object.save()

        # remove tag a
        tag_a.delete()

        # ... and commit
        transaction.commit()

        ctx['success'] = True
        ctx['message'] = _( "Successfully renamed!" )

    except Exception, e:
        transaction.rollback()

        ctx['message'] = _( "Failed, an error occurred: %(error)s" ) % { 'error': e }

    print "sending notification to user %s" % user
    notification.send( [ user ], "moderation_task_completed", ctx )
