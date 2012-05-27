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
#-*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Q
from django.db.models.signals import post_save, pre_save

from django.contrib import admin
from datetime import datetime

from django.contrib.auth.models import User
from film20.core.models import Film, Rating
from film20.utils import cache_helper as cache
from film20.utils.functional import memoize_method

import logging
logger = logging.getLogger(__name__)

#constants
from django.conf import settings
RECOMMENDATION_ALGORITHM = getattr(settings, "RECOMMENDATION_ALGORITHM", "alg1")

class BasketManager(models.Manager):
    def user_items(self, basket_user, type=None, filter=None, empty=False):
        q = (
             Q(user__username__iexact = basket_user)
        )
        q1 = None
        order_by = "-updated_at"
        if type is None:
            if not empty:
                q1 = Q(owned__isnull=False) | Q(wishlist__isnull=False)
        elif type == "OWNED":
            q1 = (
                 Q(owned = BasketItem.OWNED)
            )
        elif type == "WISHLIST":
            q1 = (
                 Q(wishlist = BasketItem.DYING_FOR) |  Q(wishlist = BasketItem.INTERESTED)  
            )
        elif type == "SHITLIST":
            q1 = (
                 Q(wishlist = BasketItem.NOT_INTERESTED)  
            )
        else:
            raise Exception("invalid basket type: %r", type)

        films = self.get_query_set().filter(q)
        if q1:
            films = films.filter(q1)

        films = films.order_by(order_by).select_related('film')
        if filter:
            films = films.filter(film__permalink=filter)
        return films

class BasketItem(models.Model):

    objects = BasketManager()
    
    # related user
    user = models.ForeignKey(User)
    
    # related film 
    film = models.ForeignKey(Film)
    
    OWNED = 1
    NOT_OWNED = 2
    OWNED_CHOICES = (
        (OWNED, _('Owned')),
        (NOT_OWNED, _('Not owned')),
    )
    owned = models.IntegerField(choices=OWNED_CHOICES, blank=True, null=True)
    
    DYING_FOR = 1
    INTERESTED = 2
    NOT_INTERESTED = 9
    
    WISHLIST_CHOICES = (
        (DYING_FOR, _('Dying for')),
        (NOT_INTERESTED, _('Not interested')),
    )

    #WTF This is totally wrong name, I mean totally. It should be: type
    wishlist = models.IntegerField(choices=WISHLIST_CHOICES, blank=True, null=True)
     
    # the dates
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    def __init__(self, *args, **kw):
        super(BasketItem, self).__init__(*args, **kw)
        # for wishlist change detection
        self.start_wishlist = self.wishlist
    
    def show_owned(self):
        if self.owned!=None:
            return self.OWNED_CHOICES[self.owned-1][1]
        else:
            return '-'
    
    def show_wishlist(self):
        if self.wishlist!=None:
            try:
                return self.WISHLIST_CHOICES[self.wishlist-1][1]
            except:
                return '-'    
        else:
            return '-'    
    
    def on_wishlist(self):
        if self.wishlist == self.DYING_FOR:
            return True
        else:
            return False
        
    def on_shitlist(self):
        if (self.wishlist == self.NOT_INTERESTED):
            return True
        else:
            return False
    
    def is_owned(self):
        if (self.owned == self.OWNED):
            return True
        else:
            return False

    # TODO add proper __str__ or __unicode__ method as pervious one caused: http://jira.filmaster.org/browse/FLM-462

    class Meta:
        # constraint to guarantee only one user/film pair is allowed
        unique_together = ("user", "film")   

    @classmethod
    def user_basket(cls, user):
        if not hasattr(user, '_basket'):
            key = cache.Key("user_basket", user)
            user._basket = cache.get(key)
            if user._basket is None:
                basket = BasketItem.objects.filter(user=user)\
                        .filter(Q(wishlist__isnull=False) | Q(owned__isnull=False))
                user._basket = dict(
                        (b.film_id, (b.wishlist, b.owned)) for b in basket
                )
                cache.set(key, user._basket)
        return user._basket

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kw):
        cache.delete(cache.Key("user_basket", instance.user))
        if hasattr(instance.user, '_basket'):
            del instance.user._basket


    @classmethod
    def post_rating_save( cls, sender, instance, created, *args, **kwargs ):
        """
            remove film from wishlist after rating it
        """
        if instance.type == Rating.TYPE_FILM:
            try:
                basket_item = BasketItem.objects.get( film=instance.film, user=instance.user, 
                                                        wishlist=BasketItem.DYING_FOR )
                basket_item.wishlist = None
                basket_item.save()

            except BasketItem.DoesNotExist:
                pass

post_save.connect(BasketItem.post_save, sender=BasketItem)
post_save.connect(BasketItem.post_rating_save, sender=Rating)
