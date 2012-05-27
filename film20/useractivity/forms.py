from django import forms
from django.utils.translation import ugettext as _
from film20.core.models import Object
from django.forms.util import ErrorList
from film20.utils.slughifi import slughifi
from film20.core.forms import comma_split
from film20.blog.forms import RelatedObjectsField

from film20.useractivity.models import Watching, UserActivity

class ActivityForm(forms.Form):
    all_activities = forms.BooleanField(label=_("all"),
                                        widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkbox_a()'}),
                                        required=False)
    reviews = forms.BooleanField(label=_("reviews"),
                                 widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxa()'}),
                                 required=False)
    most_interesting_reviews = forms.BooleanField(label=_("most interesting posts"),
                                         widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxmi()'}),
                                                  required=False)
    shorts = forms.BooleanField(label=_("short reviews"),
                                widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxa()'}),
                                required=False)
    comments = forms.BooleanField(label=_("comments"),
                                  widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxa()'}),
                                  required=False)
    links = forms.BooleanField(label=_("links"),
                               widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxa()'}),
                               required=False)
    
    all_users = forms.BooleanField(label=_("all users"),
                                   widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkbox_u()'}),
                                   required=False)
    followed = forms.BooleanField(label=_("followers"),
                                  widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxu()'}),
                                  required=False)
    similar_taste = forms.BooleanField(label=_("similar taste"),
                                       widget=forms.CheckboxInput(attrs={'onclick':'javascript:planet_checkboxu()'}),
                                       required=False)
    
    favorites = forms.BooleanField(label=_("favorites"), widget=forms.CheckboxInput(),required=False)

class FakeActivityForm():
    all_activities = None
    reviews = None
    most_interesting_reviews = None
    shorts = None
    comments = None
    links = None
    
    all_users = None
    followed = None
    similar_taste = None

    favorites = None
    
    def __init__(self, all_activities=None, reviews=None, shorts=None, comments=None,
                 links=None, all_users=None, followed=None, similar_taste=None,
                 favorites=None, most_interesting_reviews=None):
        
        self.all_activities = all_activities
        self.reviews = reviews
        self.most_interesting_reviews = most_interesting_reviews
        self.shorts = shorts
        self.comments = comments
        self.links = links
        self.all_users = all_users
        self.followed = followed
        self.similar_taste = similar_taste
        self.favorites = favorites
    
    def is_empty_form(self):
        return (self.all_activities == None) & (self.reviews == None) & (self.shorts == None) &\
        (self.comments == None) & (self.links == None) & (self.all_users == None) & (self.followed == None) &\
        (self.similar_taste == None) &(self.favorites == None) &(self.most_interesting_reviews == None)

class FakeMenuForm():
    all_activities = None
    reviews = None
    shorts = None
    comments = None
    links = None
    most_interesting_reviews = None
    
    def __init__(self, all_activities=None, reviews=None, shorts=None,
                 comments=None, links=None, most_interesting_reviews = None):

        self.all_activities = all_activities
        self.reviews = reviews
        self.shorts = shorts
        self.comments = comments
        self.links = links
        self.most_interesting_reviews = most_interesting_reviews
    
    def is_empty_form(self):
        return (self.all_activities == None) & (self.reviews == None) & (self.shorts == None) &\
                (self.comments == None) & (self.links == None)& (self.most_interesting_reviews == None)   
    
class SuperForm(forms.Form):
    body = forms.CharField(label=_('Review'), widget=forms.Textarea(attrs={
                                                    'onfocus':'javascript:make_blue(this)',
                                                    'onblur':'javascript:make_grey(this)',
                                                    'class':'gray_border'
                                                    }))
    related_film = RelatedObjectsField( max_length=255,
                                        required=False,
                                        widget=forms.TextInput(attrs={
                                            'size':'53',
                                            'onfocus':'javascript:make_blue(this)',
                                            'onblur':'javascript:make_grey(this)',
                                            'class':'gray_border'
                                            }
                                    ))

    def clean_body(self):
        body = self.cleaned_data['body']
        if len(body) < 4:
            raise forms.ValidationError(_('Note cannot be shorter than 4 characters!'))
        else:
            return self.cleaned_data['body']

    def clean_related_film(self):
        related = []
        related_film_form_data = self.cleaned_data['related_film']
        if isinstance(related_film_form_data, (list, tuple)):
            return related_film_form_data
        if len(related_film_form_data) ==0:
            self.cleaned_data['related_film'] == ""
            return self.cleaned_data['related_film']
        else:
            from re import compile
            year_pattern = compile( r'\[(\d+)\]$' )
            for related_film in comma_split(related_film_form_data):

                films = search_film( year_pattern.sub( '', related_film ) )

                def match_film(film):
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
                        msg.extend(u"%s [%d]"%(unicode(f), f.release_year) for f in films)
                        self._errors["related_film"] = ErrorList(msg)
                    else:
                      related.append(matches[0])
                else:
                    msg = _('Movie') +" "+  related_film +" "+ _('is not present in the database')
                    self._errors["related_film"] = ErrorList([msg])
        return related

class SubscribeForm(forms.Form):
    activity = forms.CharField(max_length=16, widget=forms.HiddenInput)
    is_observed = forms.BooleanField(label=_("Is observed"), required=False)

    def __init__(self, data=None, activity=None, user=None):
        self.user = user
        if activity:
            initial = {
                    'is_observed': Watching.is_subscribed(activity, user),
                    'activity': activity.id,
            }
        else:
            initial = None
        super(SubscribeForm, self).__init__(data, initial=initial)

    def clean_activity(self):
        id = self.cleaned_data['activity']
        try:
            return UserActivity.objects.get(id=id)
        except UserActivity.DoesNotExist, e:
            raise forms.ValidationError(str(e))

    def save(self):
        activity = self.cleaned_data['activity']
        Watching.subscribe(activity, self.user, self.cleaned_data['is_observed'])

