#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
from django.db import models
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from film20.core.models import Film
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE
import logging
logger = logging.getLogger(__name__)
from film20.utils.cache_helper import delete_cache, CACHE_SHOP_ITEM_FOR_FILM

class ItemManager(models.Manager):
    def get_query_set(self):
        return super(ItemManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)

class Item(models.Model):
    """
        Shops that we integrate with
    """

    film = models.ForeignKey(Film)

    # official festival name
    external_id = models.CharField(_('Title'), max_length=200)
    url_product = models.CharField(_('URL Product'), max_length=200)
    url_add_to_basket = models.CharField(_('URL Add To Basket'), max_length=200, blank=True, null=True)
    url_image = models.CharField(_('URL Image'), max_length=200, blank=True, null=True)

    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    # TODO: if more shops are added, add new field 'item_kind'
    # TODO: and update the constraint one_item_for_film to allow one item per film per kind
    # TODO: (currently it allows one per film)

    # assign manager
    objects = ItemManager()

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    def save(self):
        super(Item, self).save()
        logger.debug("saving item: %s" % self.id)
        delete_cache(CACHE_SHOP_ITEM_FOR_FILM, self.film.id)

    def __unicode__(self):
        return unicode(self.id)
    
class ItemAdmin(admin.ModelAdmin):
    pass
