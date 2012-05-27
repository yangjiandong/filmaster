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
from django import forms
from film20.blog.models import Blog, Post
from django.utils.translation import ugettext as _
from django.forms.util import ErrorList
from django.db.models import Q

from film20.search import search_film
from film20.core.forms import *

from film20.utils.slughifi import slughifi

class BlogSettingsForm(forms.Form):

    blog_title = forms.CharField(widget=forms.TextInput(), max_length=200,required=False, label=_('Blog title'))

# API friendly form field
class RelatedObjectsField(forms.CharField):
    def clean(self, value):
        if isinstance(value, (list, tuple)):
            return value
        return super(RelatedObjectsField, self).clean(value)
        
class BlogPostForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'onfocus':'javascript:make_blue(this)','onblur':'javascript:make_grey(this)','class':'gray_border'}))
    lead = forms.CharField(required=False, widget=forms.Textarea(attrs={'onfocus':'javascript:make_blue(this)','onblur':'javascript:make_grey(this)','class':'gray_border'}))
    body = forms.CharField(widget=forms.Textarea(attrs={'onfocus':'javascript:make_blue(this)','onblur':'javascript:make_grey(this)','class':'gray_border'}))
    related_film = RelatedObjectsField(max_length=255,required=False,widget=forms.TextInput(attrs={'size':'53','onfocus':'javascript:make_blue(this)','onblur':'javascript:make_grey(this)','class':'gray_border'}))
    related_person = RelatedObjectsField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'size':'53','onfocus':'javascript:make_blue(this)','onblur':'javascript:make_grey(this)','class':'gray_border'}))    

    class Meta:
    	model = Post
        exclude = ('creator_ip', 'created_at', 'updated_at', 'publish', 'permalink', 'type', 'status', 'version','featured_note','LANG', 'is_public', 'is_published','status','number_of_comments','user')
        
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(BlogPostForm, self).__init__(*args, **kwargs)
        
    def clean_title(self):
        if not self.instance.pk:
            permalink = slughifi(self.cleaned_data['title'])
            if Post.objects.filter(Q(user=self.user), Q(permalink=permalink), Q(status = Post.PUBLIC_STATUS)|Q(status = Post.DRAFT_STATUS)).count():
                raise forms.ValidationError(_('Title must be unique!'))
            return self.cleaned_data['title']
        try:
            permalink = slughifi(self.cleaned_data['title'])
            post = Post.objects.get(Q(user=self.user), Q(permalink=permalink), Q(status = Post.PUBLIC_STATUS)|Q(status = Post.DRAFT_STATUS))
            if post != self.instance:
                raise forms.ValidationError(_('Title must be unique!'))
        except Post.DoesNotExist:
            pass
        return self.cleaned_data['title']  
      
    def clean_body(self):
        body = self.cleaned_data['body']
        if len(body) < 4:
            raise forms.ValidationError(_('Article cannot be shorter than 4 characters!'))
        else:                 
            return self.cleaned_data['body']
    
    def clean_lead(self):
        lead = self.cleaned_data['lead']
        if lead:
            if len(lead) < 4:
                raise forms.ValidationError(_('Lead cannot be shorter than 4 characters!'))
            else:
                return self.cleaned_data['lead']
        else:
             return self.cleaned_data['lead']   
    
           
    def clean_related_film(self):
        related = []
        related_film_form_data = self.cleaned_data['related_film']
        if isinstance(related_film_form_data, (list, tuple)):
            return related_film_form_data
        if len(related_film_form_data) == 0:
            self.cleaned_data['related_film'] == ""
            return self.cleaned_data['related_film']
        else:
            from re import compile
            year_pattern = compile( r'\[(\d+)\]$' )
            for related_film in comma_split(related_film_form_data):
                films = search_film( year_pattern.sub( '', related_film ) )

                def match_film(film):
                    if not film:
                        return False
                    localized_title = film.get_localized_title()
                    return related_film in [film.title,
                                            localized_title,
                                            u"%s [%d]"%(film.title, film.release_year),
                                            u"%s [%d]"%(localized_title, film.release_year)]
                
                if films:
                    matches = filter(match_film, films)
                    if not matches or len(matches)>1:
                        msg = []
                        if not matches:
                            msg.append(_('Movie') + " " + related_film + " " + _('is not present in the database!'))
                        msg.append(_('Maybe you were looking for these movies') + ": ")
                        msg.extend(unicode(f) for f in films)
                        self._errors["related_film"] = ErrorList(msg)
                    else:
                      related.append(matches[0])
                else:
                    msg = _('Movie') +" "+  related_film +" "+ _('is not present in the database')
                    self._errors["related_film"] = ErrorList([msg]) 
        return related
    
    def clean_related_person(self):
        return do_clean_related_person(self)
        

