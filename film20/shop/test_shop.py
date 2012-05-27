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
import unittest

from film20.core.models import Film, Object
from film20.shop.models import *
from film20.shop.shop_helper import *
from film20.utils.test import TestCase

class ShopTestCase(TestCase):
    film1 = None
    film2 = None
    item1 = None

    def clean_data(self):
        Film.objects.all().delete()

    def initialize(self):
        self.clean_data()

        film1 = Film()
        film1.id = 1
        film1.title = "Battlefield Earth"
        film1.type = Object.TYPE_FILM
        film1.permalink = "battlefield-earth-i"
        film1.release_year = 2010
        film1.save()
        self.film1 = film1

        film2 = Film()
        film2.id = 2
        film2.title = "Battlefield Earth II"
        film2.type = Object.TYPE_FILM
        film2.permalink = "battlefield-earth-ii"
        film2.release_year = 2001
        film2.save()
        self.film2 = film2

        item = Item()
        item.film = film1
        item.external_id = '232323'
        item.url_product = 'http://www.amazonka.pl/2046_wong-kar-wai,99900073479.bhtml'
        item.save()
        self.item1 = item

    def test_get_item_for_film(self):
        """
            Tests getting the item for film
        """
        self.initialize()
        
        shop_helper = ShopHelper()
        the_item = shop_helper.get_item_for_film(self.film1)
        self.assertEquals(the_item.film, self.film1)
        self.assertEquals(the_item.url_product, self.item1.url_product)
        self.assertEquals(the_item, self.item1)

    def test_import_items(self):
        self.initialize()

        # one item exists already before importing
        count_items = Item.objects.all().count()
        self.assertEquals(count_items, 1)

        shop_helper = ShopHelper()
        shop_helper.import_items('shop/test_data/amazonka.xml')

        # after the import is done, one item should have been updated
        # and one item should have been added resulting in 2 items in db
        count_items = Item.objects.all().count()
        self.assertEquals(count_items, 2)

        # make sure the first item was actually updated (changed product url)
        item =  Item.objects.get(film=self.film1)
        self.assertEquals(item.external_id, str(99900073478))


