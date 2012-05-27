import os
from django.db import models
from film20.utils.posters import thumbnail_path, make_thumbnail

import logging
logger = logging.getLogger(__name__)

class ThumbImageFieldFile(models.ImageField.attr_class):
    @property
    def thumbnails(self):
        if self:
            return dict((size, thumbnail_path(self, size)) for size in self.field.sizes)
        else:
            return {}
    
    def make_thumbnails(self):
        return self.field.make_thumbnails(self)

class ThumbImageField(models.ImageField):
    attr_class = ThumbImageFieldFile
    def __init__(self, *args, **kw):
        self.sizes = kw.pop('thumbnails', ())
        super(ThumbImageField, self).__init__(*args, **kw)

    def pre_save(self, model_instance, add):
        value = super(ThumbImageField, self).pre_save(model_instance, add)
        if value:
            self.make_thumbnails(value)
        return value
    
    def make_thumbnails(self, value):
        for size in self.sizes:
            try:
                make_thumbnail(value, size)
            except IOError, e:
                logger.error(unicode(e))
        
