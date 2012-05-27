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
from django.utils.translation import ugettext_lazy as _
from django import forms
from film20.threadedcomments.models import DEFAULT_MAX_COMMENT_LENGTH
from film20.threadedcomments.models import FreeThreadedComment, ThreadedComment
from film20.threadedcomments.models import check_duplicate_comment

import film20.settings as settings
# constants
MIN_CHARACTERS_COMMENT_APPLY = getattr(settings, "MIN_CHARACTERS_COMMENT_APPLY", True)
MIN_CHARACTERS_COMMENT = getattr(settings, "MIN_CHARACTERS_COMMENT", 10)

import logging
logger = logging.getLogger(__name__)

class ThreadedCommentForm(forms.ModelForm):
    """
    Form which can be used to validate data for a new ThreadedComment.
    It consists of just two fields: ``comment``, and ``markup``.
    
    The ``comment`` field is the only one which is required.
    """

    comment = forms.CharField(
        label = _('comment'),
        max_length = DEFAULT_MAX_COMMENT_LENGTH,
        widget = forms.Textarea({'class':'reply-textarea'})
    )

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')

        if MIN_CHARACTERS_COMMENT_APPLY:
            if len(comment)<MIN_CHARACTERS_COMMENT:
                raise forms.ValidationError(_("Comments cannot be shorter than %s characters!" % MIN_CHARACTERS_COMMENT))

        if (check_duplicate_comment(comment)):
            raise forms.ValidationError(_("It looks like you have already said that!"))

        return comment

    class Meta:
        model = ThreadedComment
        fields = ('comment', 'markup')

class FreeThreadedCommentForm(forms.ModelForm):
    """
    Form which can be used to validate data for a new FreeThreadedComment.
    It consists of just a few fields: ``comment``, ``name``, ``website``,
    ``email``, and ``markup``.
    
    The fields ``comment``, and ``name`` are the only ones which are required.
    """

    comment = forms.CharField(
        label = _('comment'),
        max_length = DEFAULT_MAX_COMMENT_LENGTH,
        widget = forms.Textarea
    )

    class Meta:
        model = FreeThreadedComment
        fields = ('comment', 'name', 'website', 'email', 'markup')
