from film20.userprofile.models import Avatar, AVATAR_SIZES
from django.contrib.auth.models import User
from django.conf import settings
try:
    from PIL import Image
except:
    import Image

import os
import time
import logging
logger = logging.getLogger(__name__)

from film20.utils.cache_helper import *
from film20.utils.slughifi import slughifi

def _parse(size):
    return size == 'auto' and size or int(size)

def parse_size(size):
    if isinstance(size, (tuple, list)) and len(size) == 2:
        ret = _parse(size[0]), _parse(size[1])
        return ret
    if isinstance(size, (long, int)):
        return size, 'auto'
    raise ValueError('invalid size spec')

import re
SIZE_RE = re.compile(r"\.(\d+|auto)x(\d+|auto)$")

def thumbnail_path(image, size):
    base, ext = os.path.splitext(unicode(image))
    size = parse_size(size)
    if size == ('auto', 'auto'):
        return unicode(image)
    m = SIZE_RE.search(base)
    if m:
        base = base[0:-len(m.group(0))]
    return "%s.%sx%s%s" % (base, size[0], size[1], ext)

def make_thumbnail(image, size):
    """
        image must be relative to MEDIA_ROOT folder (ImageFieldFile or str/unicode)
        size - (W, H) tuple
    """    
    image = unicode(image)
    size = parse_size(size)
    thumb_path = thumbnail_path(image, size)
    abs_thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_path)

    if not os.path.exists(abs_thumb_path):
        try:
            img = Image.open(os.path.join(settings.MEDIA_ROOT, image))
    
            dest_w, dest_h = size
            w, h = img.size
    
            if isinstance(dest_w, (int, long)) and isinstance(dest_h, (int, long)):
                if h * dest_w > dest_h * w:
                    # keep width, cut height
                    new_h = w * dest_h / dest_w
                    top = (h - new_h) / 2
                    crop = (0, top, w, top + new_h)
                else:
                    new_w = h * dest_w / dest_h
                    left = (w - new_w) / 2
                    crop = (left, 0, left + new_w, h)
                img = img.crop(crop)
            elif dest_h == 'auto':
                size = (dest_w, dest_w * h / w)
            elif dest_w == 'auto':
                size = (dest_h * w / h, dest_h)
            else:
                assert False
    
            img = img.resize(size, Image.ANTIALIAS)
            img.save(abs_thumb_path, image.lower().endswith('.png') and "PNG" or "JPEG")
            logger.debug("new thumbnail saved: %s", thumb_path)
        except:
            logger.error("image %s doesnt exist" % image)
    else:
        logger.debug("thumbnail %s already exists", thumb_path)
    return thumb_path

def _exists(path):
    return os.path.isfile(os.path.join(settings.MEDIA_ROOT, path))

def get_image_path(the_object, size_x='auto', size_y='auto'):
    type = getattr( the_object, 'type', None )
    if type and the_object.type == the_object.TYPE_PERSON:
        default_path = settings.DEFAULT_PHOTO
    else:
        default_path = settings.DEFAULT_POSTER
    
    paths = [ 'poster', 'image' ]
    for p in paths:
        path = getattr( the_object, p, None )
        if path: 
            break
    path = path or default_path

    try:
        thumb = make_thumbnail(path, (size_x, size_y))
    except Exception, e:
        logger.warning(unicode(e))
        thumb = make_thumbnail(default_path, (size_x, size_y))

    return os.path.join(settings.MEDIA_URL, thumb)

def is_image_valid(abs_path):
    try:
        i=Image.open(abs_path); cropped = i.crop((0,0) + tuple(i.size))
    except Exception, e:
        logger.warning("%s", unicode(e))
        return False
    return True
