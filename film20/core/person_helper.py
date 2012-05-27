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
from django.db.models import Q
from django import forms

from film20.core.models import Person
from film20.core.object_helper import *

from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

import logging
logger = logging.getLogger(__name__)

NUMBER_OF_ITEMS_PUBLIC_PROFILE= 5

class PersonHelper(ObjectHelper):
    """
    
    """    
    def get_person(self, permalink):
        return Person.objects.select_related().get(parent__permalink=permalink, parent__status=1) 
        
    def get_person_tag_form(self, the_film, POST=None):
        return super.get_object_tag_form(the_film, POST)
    
    def get_films_played(self, the_person):
        list = None
        query = (
            Q(person=the_person) &
            Q(LANG=LANGUAGE_CODE)
        )
        list = Character.objects.filter(query).order_by("-film__release_year")
        return list
    
    def get_films_directed(self, the_person):
        list = None
        query = (
            Q(directors=the_person)
        )
        list = Film.objects.filter(query).order_by("-release_year").distinct()
        return list
        
    def get_related_posts(self, permalink):
        from film20.blog.models import Post 
        related_posts = Post.objects.select_related()
        related_posts = related_posts.filter(related_person__permalink = permalink)
        related_posts = related_posts.filter(status=Post.PUBLIC_STATUS)
        
        related_posts = related_posts.extra(
            select={
                    'related_person_count': 'select count(*) from blog_post_related_person where post_id=blog_post.parent_id'
            },
        )
        
        related_posts = related_posts.order_by("related_person_count")
        related_posts = related_posts.order_by("blog_post.publish")
        related_posts = related_posts[:2]
        
        return related_posts
    
    def get_favorite_actors(self, user):        
        """ 
        Fetch user's favorite actors
        """        
        
        # TODO: optimize -- a query is executed for each person now!!
        qset = (
            Q(user=user) &
            Q(type=Rating.TYPE_ACTOR) &
            Q(rating__isnull = False) &
            Q(actor__permalink__isnull = False)
        )
        favorite_people = Rating.objects.select_related("person").filter(qset).order_by('-rating')[:NUMBER_OF_ITEMS_PUBLIC_PROFILE]
        return favorite_people
    
    def get_favorite_directors(self, user):
        """ 
        Fetch user's favorite directors
        """        
        
        # TODO: optimize -- a query is executed for each person now!!
        qset = (
            Q(user=user) &
            Q(type=Rating.TYPE_DIRECTOR) &
            Q(rating__isnull = False) &
            Q(director__permalink__isnull = False)
        )
        favorite_people = Rating.objects.select_related("person").filter(qset).order_by('-rating')[:NUMBER_OF_ITEMS_PUBLIC_PROFILE]
        return favorite_people

    def get_person_localized_form(self, the_person, POST=None):
        if POST==None:
            localized = the_person.get_localized_person()
            return PersonLocalizedForm(
                initial = {
                    'localized_name': localized and localized.name or '',
                    'localized_surname': localized and localized.surname or '',
                }
            )
        else:
            return PersonLocalizedForm(POST)
            
    def handle_edit_person_localized(self, the_person, the_form):
        """
        Handles the localized person editing form.
        """
        is_valid = the_form.is_valid()
        
        if is_valid:
            from film20.core.models import PersonLocalized
            name = the_form.cleaned_data['localized_name']
            surname = the_form.cleaned_data['localized_surname']
            localized, created = PersonLocalized.objects.get_or_create(
                person=the_person,
                parent=the_person,
                defaults = {
                    'name':name,
                    'surname':surname,
                },
            )
            if not created:
                localized.name = name
                localized.surname = surname
                localized.save()
        return is_valid
          
          
class PersonLocalizedForm(forms.Form):
    localized_name = forms.CharField(label=_("Name"), max_length=50, widget=forms.TextInput({'class':'text'}),)
    localized_surname = forms.CharField(label=_("Surname"), max_length=50, widget=forms.TextInput({'class':'text'}))
    
    def clean_localized_name(self):
        return self.validate_field('localized_name')

    def clean_localized_surname(self):
        return self.validate_field('localized_surname')
          
    def validate_field(self, field):
        s = self.cleaned_data.get(field)
        if s:
            if len(s)==0:
                raise forms.ValidationError(_("Name and surname cannot be empty strings!"))
            elif len(s)>50:
                raise forms.ValidationError(_("Name and surname cannot be longer than 50 characters!"))
            else:
                return s
        else:
            return None
