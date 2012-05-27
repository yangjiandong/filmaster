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

from film20.core.models import Object, Rating, Film, Person

import logging
logger = logging.getLogger(__name__)

class Event(Object):
    STATUS_OPEN = 1
    STATUS_CLOSED = 2
    EVENT_STATUS_CHOICES = (
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
    )
    parent = models.OneToOneField(Object, parent_link=True)
    title = models.CharField(_('Title'), max_length=200)
    lead = models.TextField(_('Lead'), blank=True)
    body = models.TextField(_('Body'))
    event_status = models.IntegerField(choices=EVENT_STATUS_CHOICES)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'),auto_now=True)

    class Meta:
        get_latest_by = 'created_at'
        ordering = ('-created_at',)

    def is_closed(self):
      return self.event_status == Event.STATUS_CLOSED

    def __unicode__(self):
        return self.title
    
class EventAdmin(admin.ModelAdmin):
  pass

class NominatedManager(models.Manager):
  def with_rates(self,event):
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute("""
      SELECT n.id, n.film_id, n.person_id, n.type, n.oscar_type, r.average_score as avg, r.number_of_votes as count
      FROM event_nominated n LEFT JOIN core_filmranking r 
      ON n.type = r.type and n.film_id = r.film_id and (r.actor_id is null and n.person_id is null or r.actor_id=n.person_id)
      WHERE n.event_id = %d
      ORDER BY n.oscar_type,avg desc
    """%event.pk);
    result_list = []
    for row in cursor.fetchall():
      p = self.model(id=row[0], film_id = row[1], person_id = row[2], type = row[3], oscar_type=row[4])
      p.avg_rating = "%3.1f"%(row[5] or 0)
      p.count = row[6]
      result_list.append(p)

    # http://www.mail-archive.com/django-users@googlegroups.com/msg92582.html
    connection._rollback()
    
    return result_list
      
class Nominated(models.Model):
    objects = NominatedManager()
    
    event = models.ForeignKey(Event, blank=False, null=False, related_name="nominations")
    film = models.ForeignKey(Film, blank=False, null=False, related_name="film_nominated")
    person = models.ForeignKey(Person, blank=True, null=True, related_name="person_nominated")

    # TODO: rename as they don't necessarily belong to Oscars only
    OSCAR_CATEGORIES = (
      (1,_('Best Film'),Rating.TYPE_FILM),
      (2,_('Director'),Rating.TYPE_EXTRA_DIRECTORY),
      (3,_('Actor in a Leading Role'),Rating.TYPE_ACTOR_IN_FILM),
      (4,_('Actress in a Leading Role'),Rating.TYPE_ACTOR_IN_FILM),
      (5,_('Actor in a Supporting Role'),Rating.TYPE_ACTOR_IN_FILM),
      (6,_('Actress in a Supporting Role'),Rating.TYPE_ACTOR_IN_FILM),
      (7,_('Writing (Original Screenplay)'),Rating.TYPE_EXTRA_SCREENPLAY),
      (8,_('Writing (Adapted Screenplay)'),Rating.TYPE_EXTRA_SCREENPLAY),
      (9,_('Visual Effects'),Rating.TYPE_EXTRA_SPECIAL_EFFECTS),
      (10,_('Music'),Rating.TYPE_EXTRA_MUSIC),
      (11,_('Cinematography'),Rating.TYPE_EXTRA_CAMERA),
      (12,_('Editing'),Rating.TYPE_EXTRA_EDITING),
      (13,_('Best Animated Feature Film'),Rating.TYPE_FILM),
      (14,_('Best Foreign Language Film'),Rating.TYPE_FILM),
      # non-oscar
      (15,_('Best Comedy or Musical'),Rating.TYPE_FILM),
      (16,_('Best Drama'),Rating.TYPE_FILM),
      (17,_('Best Sci-Fi or Fantasy'),Rating.TYPE_FILM),
      (18,_('Best Polish'),Rating.TYPE_FILM),
      (19,_('Best Action Film'),Rating.TYPE_FILM),
      (20,_('Best Dialogues'),Rating.TYPE_DIALOGUES),
      (21,_('Best Short Film'),Rating.TYPE_FILM),
      (22,_('Best Documentary'),Rating.TYPE_FILM),
      (50,_('Most Ridiculous Translation'),Rating.TYPE_MOST_RIDICULOUS_TRANSLATION),
      (51,_('Worst Film'),Rating.TYPE_FILM),
    )

    OSCAR_CHOICES = map(lambda x:x[:2],OSCAR_CATEGORIES)
    
    type = models.IntegerField(choices=Rating.ALL_RATING_TYPES)
    oscar_type = models.IntegerField(choices=OSCAR_CHOICES)
    
    RATING_MAP = dict(map(lambda x:(x[0],x[2]),OSCAR_CATEGORIES))
    DESCR_MAP = dict(OSCAR_CHOICES)
    
#http://www.oscar.com/nominees/?pn=nominees
    
    def get_category_name(self):
      return self.DESCR_MAP[self.oscar_type] if self.oscar_type in self.DESCR_MAP else ("unknknown type: %d"%self.oscar_type)

    def get_rating_type(self):
      return self.RATING_MAP[self.oscar_type]

      
    def save(self):
      self.type = self.get_rating_type()
      super(Nominated,self).save()
          
class NominatedAdmin(admin.ModelAdmin):
  exclude = ['type']
  raw_id_fields = ['film','person']
  list_display = ['film','person','oscar_type']
