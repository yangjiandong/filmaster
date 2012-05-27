#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2010 Filmaster (Borys Musielak, Adam Zielinski).
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
from django.utils.translation import gettext_lazy as _

from film20.core.models import Film
from film20.shop.models import Item
from film20.utils.cache_helper import get_cache, set_cache, delete_cache, CACHE_SHOP_ITEM_FOR_FILM

import logging
logger = logging.getLogger(__name__)


class ShopHelper:
    """
    A ``Helper`` object for shop integration to facilitate common static operations
    """

    def get_item_for_film(self, the_film):
        """
            Returns the shop item for given film or None if not set
        """
        the_item = get_cache(CACHE_SHOP_ITEM_FOR_FILM, the_film.id)
        if the_item is not None:
            logger.debug("got shop item from cache!")
            return the_item

        try:
            the_item = Item.objects.get(
                film=the_film
                )
        except Item.DoesNotExist:
            # everything is fine
            the_item = None

        # cache only if set
        if the_item is not None:
            set_cache(CACHE_SHOP_ITEM_FOR_FILM, the_item.film.id, the_item)
        return the_item

    def import_items(self, filename):
        from xml.dom import minidom

        # Real url: http://www.amazonka.pl/exportxml/filmaster/ekxmmnfpcu/out.films.xml.gz

        inserted = 0
        updated = 0
        failed = 0

        # Open XML document using minidom parser
        DOMTree = minidom.parse(filename)

        # iterate through XML file
        cNodes = DOMTree.childNodes
        for i in cNodes[0].getElementsByTagName("film"):

            import string
            film_url = i.getElementsByTagName("url")[0].childNodes[0].toxml()
            film_url = string.replace(film_url, "http://filmaster.pl/film/", "")
            film_url = film_url[0:len(film_url)-1]

            try:
                the_film =  Film.objects.get(parent__permalink=film_url)
            except Film.DoesNotExist:
                failed = failed + 1
                # everything is fine
                print "Film does not exist! ID = %s" % film_url
                continue

            try:
                item =  Item.objects.get(film=the_film)
                updated = updated + 1
            except Item.DoesNotExist:
                # everything is fine (assigning new item)
                inserted = inserted + 1
                item = Item()
                item.film = the_film

            item.external_id = i.getElementsByTagName("amazonka-id")[0].childNodes[0].toxml()
            item.url_product = i.getElementsByTagName("amazonka-url-produkt")[0].childNodes[0].toxml()
            item.url_add_to_basket = i.getElementsByTagName("amazonka-url-koszyk")[0].childNodes[0].toxml()
            try:
                item.url_image = i.getElementsByTagName("amazonka-url-zdjecie")[0].childNodes[0].toxml()
            except IndexError, e:
                # it's ok, image is not required
                pass

            item.save()

        print "Importing films finished"
        print "Inserted %s new shop items." % inserted
        print "Updated %s existing shop items." % updated
        print "And %s shop items failed to import." % failed
