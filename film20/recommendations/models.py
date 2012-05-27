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

from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
from film20.core.models import Film
from film20.utils import cache

class Computed(models.Model):
    """
        Stores the last time the recommendations were computed
    """
    # user
    user = models.ForeignKey(User)
    
    comparators = models.IntegerField(blank=True, null=True)
    recommendations = models.IntegerField(blank=True, null=True)
    
    # the dates
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

class RecommendationVote(models.Model):
    user = models.ForeignKey(User)
    film = models.ForeignKey(Film)
    
    average_rating = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    number_of_ratings = models.IntegerField(default=0)
    ratings_based_prediction = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    traits_based_prediction = models.DecimalField(max_digits=6, decimal_places=4, null=True)
    
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    VOTE_CHOICES = (
            (0, _("No")),
            (1, _("Yes")),
    )
    vote = models.IntegerField(default=0, choices = VOTE_CHOICES, null=True)

    @classmethod
    def get_unliked_film_ids(cls, user):
        if not user.id:
            return ()
        key = cache.Key("unliked_recommendations", user.id)
        ret = cache.get(key)
        if ret is None:
            ret = cls.objects.filter(user=user, vote=0).values_list('film_id', flat=True)
            cache.set(key, ret)
        return ret

    @classmethod
    def post_save(cls, sender, instance, created, *args, **kw):
        cache.delete(cache.Key("unliked_recommendations", instance.user_id))

models.signals.post_save.connect(RecommendationVote.post_save, sender=RecommendationVote)
