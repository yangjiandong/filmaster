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
from django.contrib.auth.models import User
from django.contrib import admin
from datetime import datetime
from django.utils.translation import gettext_lazy as _

from film20.core.models import Object, Character
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE
from film20.config.urls import urls
import logging
logger = logging.getLogger(__name__)

class ContestManager(models.Manager):
    def get_query_set(self):
        return super(ContestManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)

class Contest(Object):
    """
        Festival object representing film festial and other events
        represented on Filmaster
    """
    STATUS_OPEN = 1
    STATUS_CLOSED = 2
    CONTEST_STATUS_CHOICES = (
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
    )
    parent = models.OneToOneField(Object, parent_link=True)

    # official festival name
    name = models.CharField(_('Name'), max_length=200)
    lead = models.TextField(_('Lead'), blank=True, null=True)
    body = models.TextField(_('Body'), blank=True, null=True)

    start_date = models.DateField(_('Starts on'),)
    end_date = models.DateField(_('Ends on'),)

    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    # assign manager
    objects = ContestManager()
    
    event_status = models.IntegerField(choices=CONTEST_STATUS_CHOICES)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        get_latest_by = 'start_date'
        ordering = ('-start_date',)

    def is_closed(self):
      return self.event_status == Contest.STATUS_CLOSED

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return '/'+urls["SHOW_CONTEST"]+'/'+self.permalink
    
class ContestAdmin(admin.ModelAdmin):
    pass

class GameManager(models.Manager):
    def get_query_set(self):
        return super(GameManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)
        
class Game(Object):
    """
        A game between two Characters assigned to some Contest.
    """
    parent = models.OneToOneField(Object, parent_link=True)
    contest = parent_game = models.ForeignKey(Contest)
    parent_game = parent_game = models.ForeignKey('self', blank=True, null=True)

    LEVEL_32 = 32
    LEVEL_16 = 16
    LEVEL_8 = 8
    QUARTER_FINAL = 4
    SEMI_FINAL = 2
    FINAL = 1

    LEVEL_CHOICES = (
        (LEVEL_32, '1/32'),
        (LEVEL_16, '1/16'),
        (LEVEL_8, '1/8'),
        (QUARTER_FINAL, _('Quarter-final')),
        (SEMI_FINAL, _('Semi-final')),
        (FINAL, _('Final'))
    )

    character1 = models.ForeignKey(Character, related_name='first character', blank=True, null=True)
    character2 = models.ForeignKey(Character, related_name='second character',blank=True, null=True)
    character1score = models.IntegerField(default=0)
    character2score = models.IntegerField(default=0)
    winner = models.ForeignKey(Character, related_name='the winner',blank=True, null=True)

    start_date = models.DateField(_('Starts on'),)
    end_date = models.DateField(_('Ends on'),)

    # language
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)

    # assign manager
    objects = GameManager()

    level = models.IntegerField(choices=LEVEL_CHOICES)

    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)


    def __unicode__(self):
        return unicode(self.character1.character) + " vs " + unicode(self.character2.character)

    def get_absolute_url(self):
        if self.contest:
            return "/"+urls["SHOW_CONTEST"] +"/" + self.contest.permalink + "/" + urls['SHOW_GAME'] + "/" + str(self.permalink)
        else:
            return "/"+urls["SHOW_CONTEST"] +"/" + self.parent.permalink + "/" + urls['SHOW_GAME'] + "/" + str(self.permalink)

    def get_title(self):
        return unicode(self.character1.character) + " vs " + unicode(self.character2.character)



class GameAdmin(admin.ModelAdmin):
    raw_id_fields = ['character1', 'character2', 'winner', ]


class GameVote(models.Model):
    """
        A single vote for one of the characters in a given game.
    """
    game = models.ForeignKey(Game)
    character = models.ForeignKey(Character)
    user = models.ForeignKey(User)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

class GameVoteAdmin(admin.ModelAdmin):
    raw_id_fields = ['character', ]




