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
from django import forms

from film20.config.const import *
from film20.core.models import Rating, ShortReview
from film20.filmbasket.models import BasketItem

import re

import logging
logger = logging.getLogger(__name__)

class RatingForm(forms.Form):
        
    FORM_TYPES = Rating.RATING_TYPES
     
    rating = forms.CharField()
    object_id = forms.CharField(widget=forms.HiddenInput)
    actor_id = forms.CharField(widget=forms.HiddenInput,required=False)
    edit_id = forms.CharField(widget=forms.HiddenInput, required=False)
    form_type = forms.CharField(widget=forms.HiddenInput)
    cancel_rating = forms.CharField(widget=forms.HiddenInput, required=False)
        
    def __init__(self, *args, **kwargs):
        super(RatingForm, self).__init__(*args, **kwargs)
        initial = kwargs.pop('initial', None)
        
        form = None
        try:
            form = args[0]
        except IndexError:
            None
        
        # in case one of the parameters is 'initial', we're setting the form prefix automatically
        # to the 'form_type' element of the 'initial' param 
        if initial:
            logger.debug("Hack: ustawiam prefix na podstawie form_type!")            
            if initial['form_type']:
                self.prefix = '%s-%s'%(initial['form_type'],initial['object_id'])
                if 'actor_id' in initial:
                  self.prefix += ('-%s'%initial['actor_id'])
                logger.debug("Prefix ustawiony na " + unicode(self.prefix))
            else:
                logger.error("Nie ma form_type w initial! Masakra!")
        # in case we have the parsed form, the prefix is set to the form_id of the processed form
        if form:
            logger.debug("Hack: ustawiam prefix na podstawie sparsowanego formularza!")
            try:
                self.prefix = form['form_id']
                logger.debug("Prefix ustawiony na " + unicode(self.prefix))
            except KeyError, e:
                logger.error("Nie ma form_id w form! Masakra!")
    
    def clean_rating(self):        
        rating = self.cleaned_data.get('rating', '')     
        try:
            int(rating)
        except ValueError:
            raise forms.ValidationError(_("Rating must be integer!"))
        
        # TODO: localize
        if int(rating) < VOTE_FILM_MIN:
            raise forms.ValidationError("Rating cannot be negative! It must be between "+str(VOTE_FILM_MIN)+" and "+str(VOTE_FILM_MAX)+"!")
        elif int(rating) > VOTE_FILM_MAX:
            raise forms.ValidationError("Rating cannot > "+str(VOTE_FILM_MAX)+"! It must be between "+str(VOTE_FILM_MIN)+" and "+str(VOTE_FILM_MAX)+"!")

        return int(rating)
    
    def clean_object_id(self):
        object_id = self.cleaned_data.get('object_id', '')        
        try:
            int(object_id)
        except ValueError:            
            raise forms.ValidationError(_("object_id must be integer!"))
        return int(object_id)
    
    def clean_actor_id(self):
      return self.cleaned_data.get('actor_id','')
      
    def clean_edit_id(self):
        edit_id = self.cleaned_data.get('edit_id', '')
        if edit_id:        
            try:
                int(edit_id)
                return int(edit_id)
            except ValueError:            
                raise forms.ValidationError(_("edit_id must be integer!"))
        else:
            return None
        
    def clean_cancel_rating(self):
        cancel_rating = self.cleaned_data.get('cancel_rating', '')
        if cancel_rating:        
            try:
                cancel_rating_int = int(cancel_rating)
                if not( (cancel_rating_int==1) | (cancel_rating_int==0) ):
                    raise forms.ValidationError(_("cancel_rating can be either 0 or 1!"))
                return cancel_rating_int
            except ValueError:            
                raise forms.ValidationError(_("cancel_rating has to be integer!"))
        else:
            return None
    
    def clean_form_type(self):
        form_type = self.cleaned_data.get( 'form_type', '')
        
        if not form_type:   
            raise forms.ValidationError(_("Form type must be provided!"))
        
        try:
            int(form_type)
        except ValueError:            
            raise forms.ValidationError(_("Form type must be integer!"))
                        
        if int(form_type) in self.FORM_TYPES:            
            return int(form_type)
        else:
            raise forms.ValidationError(_("Unknown form type: ") + unicode(form_type))
    
    # TODO: user? where from!!!?        
    # pass in form?
    def cleanXXX(self):
        # do this check only for NEW!!! (edit_id=None)        
        try:
            form_type = self.cleaned_data.get('form_type', '')
            parent = self.cleaned_data.get('object_id', '')
            
            # Check if rating exists for this object and user (it should not!)
            Rating.objects.get(
#                user = user.id, 
                parent = parent,
                type = form_type,
                rating__isnull = False
            )
            raise forms.ValidationError(_('Already voted for this object!'))                             
        except Rating.DoesNotExist:
            ### This is correct, should not be any rating for this, yet
            return        

class SingleRatingForm(forms.Form):
    rating = forms.CharField(required=False)
    type = forms.CharField(widget=forms.HiddenInput)
    film_id = forms.CharField(widget=forms.HiddenInput, required=False)
    actor_id = forms.CharField(widget=forms.HiddenInput, required=False)
    director_id = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, data, request, initial=None, prefix=None):
        from film20.core import rating_helper
        initial = initial or {}
        self.user = request.unique_user
        if not data:
            film_id = initial.get('film_id')
            actor_id = initial.get('actor_id')
            director_id = initial.get('director_id')
            type = initial.get('type')
            if self.user.id:
                r = rating_helper.get_rating(self.user, film_id=film_id, actor_id=actor_id, director_id=director_id, type=type)
                if r:
                    initial['rating'] = r

            prefix = 'rating_%d' % type
            if film_id:
                prefix += "_%d" % film_id
            if actor_id:
                prefix += "_%d" % actor_id
            if director_id:
                prefix += "_%d" % director_id 

        super(SingleRatingForm, self).__init__(data, initial=initial, prefix=prefix)

    RATING_PREFIX = re.compile(r"(rating(_\d+){1,4})-")

    @classmethod
    def get_form_prefixes(cls, query_dict):
        matches = (cls.RATING_PREFIX.match(k) for k in query_dict.keys())
        return set(m.group(1) for m in matches if m)

    def save(self):
        from film20.core import rating_helper
        rating_helper.rate(self.user,
                self.cleaned_data['rating'],
                type=self.cleaned_data['type'],
                film_id=self.cleaned_data['film_id'],
                actor_id=self.cleaned_data['actor_id'],
                director_id=self.cleaned_data['director_id']
        )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        try:
            return rating and int(rating) or None
        except ValueError:
            raise forms.ValidationError(_("Rating must be integer!"))

class SimpleFilmRatingForm(forms.Form):
    rating_1 = forms.CharField(required=False, label=_("Film"))
    
    dying_for = forms.BooleanField(required=False, label="Dying for")
    not_interested = forms.BooleanField(required=False, label=_("Not interested in"))
    owned = forms.BooleanField(required=False, label=_("Owned"))

    short_review = forms.CharField(required=False, label=_("Short Review"), widget=forms.Textarea, max_length=1000)
    film_id = forms.IntegerField(required=False, widget=forms.HiddenInput(attrs={'class':'film-id'}))

    def __init__(self, data, request, film, initial=None):
        initial = initial or {}
        self.film = film
        self.user = request.unique_user
        initial['film_id'] = film.id

        if not 'rating_1' in initial:
            ratings = Rating.get_user_ratings(self.user)
            r = ratings.get(self.film.id)
            if r:
                initial['rating_1'] = r
        
        if self.user.is_authenticated():
            # collections only for registered users
            basket = BasketItem.user_basket(self.user)
            item = basket.get(film.id)
            if item:
                initial['dying_for'] = item[0] == BasketItem.DYING_FOR
                initial['not_interested'] = item[0] == BasketItem.NOT_INTERESTED
                initial['owned'] = item[1] == BasketItem.OWNED

        prefix = "flm-%d" % film.id
        super(forms.Form, self).__init__(data, initial=initial, prefix=prefix)

    FLM_PREFIX = re.compile(r"flm-\d+")

    @classmethod
    def get_form_prefixes(cls, query_dict):
        matches = (cls.FLM_PREFIX.match(k) for k in query_dict.keys())
        return set(m.group(0) for m in matches if m)

    def save(self):
        data = self.cleaned_data
        for (k, v) in data.items():
            if k.startswith('rating_'):
                type = k[7:]
                self.film.rate(self.user, v, type)
        
        if self.user.is_authenticated():
            w = (data['dying_for'] and BasketItem.DYING_FOR or
                 data['not_interested'] and BasketItem.NOT_INTERESTED or None)
            owned = (data['owned'] and BasketItem.OWNED)

            item, created = BasketItem.objects.get_or_create(
                film=self.film,
                user=self.user,
                defaults = dict(
                    wishlist = w,
                    owned = owned
                )
            )
            if not created:
                item.wishlist = w
                item.owned = owned
                item.save()

            if self.cleaned_data['short_review']:
                sr = ShortReview.objects.create(
                        kind=ShortReview.WALLPOST,
                        user=self.user,
                        object=self.film,
                        review_text=self.cleaned_data['short_review'],
                        type=ShortReview.TYPE_SHORT_REVIEW,
                )
    
    def clean(self):
        for k in self.cleaned_data.keys():
            if k.startswith('rating_'):
                try:
                    v = int(self.cleaned_data[k])
                    if not (1 <= v <= 10):
                        v = None
                except:
                    v = None
                self.cleaned_data[k] = v
        if self.cleaned_data['dying_for'] and self.cleaned_data['not_interested']:
            self.cleaned_data['dying_for'] = False
            self.cleaned_data['not_interested'] = False

        if self.cleaned_data['owned']:
            self.cleaned_data['owned'] = False

        # WTF - why somethimes short_review key does not exist ?
        self.cleaned_data['short_review'] = self.cleaned_data.get('short_review', '').strip()
        data = self.cleaned_data
        return self.cleaned_data

class FilmRatingForm(SimpleFilmRatingForm):
    rating_14 = forms.CharField(required=False, label=_("Directory"))
    rating_6 = forms.CharField(required=False, label=_("Screenplay"))
    rating_15 = forms.CharField(required=False, label=_("Acting"))
    rating_7 = forms.CharField(required=False, label=_("Special Effects"))
    rating_8 = forms.CharField(required=False, label=_("Editing"))
    rating_9 = forms.CharField(required=False, label=_("Music"))
    rating_10 = forms.CharField(required=False, label=_("Camera"))
    rating_11 = forms.CharField(required=False, label=_("Novelity"))

    """
    BASKET_CHOICES = (
        (BasketItem.DYING_FOR, _("dying for")),
        (BasketItem.NOT_INTERESTED, _("not interested in")),
    )
    basket = forms.ChoiceField(widget=forms.RadioSelect, choices=BASKET_CHOICES, required=False)
    """

    def __init__(self, data, request, film, edit=False):
        from film20.core import rating_helper
        initial = {}
        if not data and request.unique_user.id:
            if edit:
                for type in (6, 7, 8, 9, 10, 11, 14, 15):
                    v = rating_helper.get_rating(user=request.unique_user, film_id=film.id, type=type)
                    if v:
                        initial['rating_%d' % type] = v

        super(FilmRatingForm, self).__init__(data, request, film, initial=initial)
