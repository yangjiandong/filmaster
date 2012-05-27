from django.core.management import call_command

from film20.core.management.base import BaseCommand
from film20.core.models import ObjectLocalized
from film20.tagging.models import TagTranslation

import logging
logger = logging.getLogger(__name__)

def is_tagged( localized, tag, lang ):
    try:
        ObjectLocalized.objects.get( parent=localized.parent, LANG=lang, tagged_items__tag__name=tag )
    except ObjectLocalized.DoesNotExist:
        logger.info("tag: %s %s %s", localized, tag, lang)
        logger.info(" `-- NOT EXISTS")
        return False
    else:
        return True

class Command( BaseCommand ):
    help = "Translates all tags."

    def handle( self, **options ):
        objects = []
        for tt in TagTranslation.objects.all():
            pl = filter( lambda o: not is_tagged( o, tt.en, 'en' ), ObjectLocalized.objects.filter( LANG='pl', tagged_items__tag__name=tt.pl ) )
            en = filter( lambda o: not is_tagged( o, tt.pl, 'pl' ), ObjectLocalized.objects.filter( LANG='en', tagged_items__tag__name=tt.en ) )
            for obj in pl + en:
                if not obj in objects:
                    objects.append( obj )

        logger.info("-- objects to save: %d", len( objects ))
        for object_localized in objects:
            if object_localized.tag_list == '':
                object_localized.tag_list = object_localized.get_tags_as_string()
            object_localized.save()
