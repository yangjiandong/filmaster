from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save, post_delete

from film20.utils import cache
from film20.settings import LANGUAGE_CODE

class FragmentManager(models.Manager):
    def get_query_set(self):
        return super(FragmentManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)

class Fragment( models.Model ):
    name = models.CharField( _( "Title" ), max_length=150 )
    key = models.SlugField( _( "Key" ), max_length=150)
    body = models.TextField( _( "Body" ), blank=True, null=True )
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    # assign manager
    objects = FragmentManager()

    class Meta:
        verbose_name = _( "Fragment" )
        verbose_name_plural = _( "Fragments" )

    def __unicode__( self ):
        return self.name

    @classmethod
    def clear_cache( cls, sender, instance, *args, **kwargs ):
        cache.delete( cache.Key( "fragments-ld-%s" % instance.key ) )
        cache.delete( cache.Key( "fragments-set-%s" % instance.key ) )

post_save.connect( Fragment.clear_cache, sender=Fragment )
post_delete.connect( Fragment.clear_cache, sender=Fragment )
