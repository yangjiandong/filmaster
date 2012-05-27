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
from django.db.models import signals
from threadedcomments.models import ThreadedComment, FreeThreadedComment, MARKUP_CHOICES
from threadedcomments.models import DEFAULT_MAX_COMMENT_LENGTH, DEFAULT_MAX_COMMENT_DEPTH
from comment_utils import moderation

MARKUP_CHOICES_IDS = [c[0] for c in MARKUP_CHOICES]


class CommentModerator(moderation.CommentModerator):
    max_comment_length = DEFAULT_MAX_COMMENT_LENGTH
    allowed_markup = MARKUP_CHOICES_IDS
    max_depth = DEFAULT_MAX_COMMENT_DEPTH

    def _is_past_max_depth(self, comment):
        i = 1
        c = comment.parent
        while c != None:
            c = c.parent
            i = i + 1
            if i > self.max_depth:
                return True
        return False

    def allow(self, comment, content_object):
        if self._is_past_max_depth(comment):
            return False
        if comment.markup not in self.allowed_markup:
            return False
        return super(CommentModerator, self).allow(comment, content_object)

    def moderate(self, comment, content_object):
        if len(comment.comment) > self.max_comment_length:
            return True
        return super(CommentModerator, self).moderate(comment, content_object)

class Moderator(moderation.Moderator):
    def connect(self):
        for model in (ThreadedComment, FreeThreadedComment):
            signals.pre_save.connect(self.pre_save_moderation, sender=model)
            signals.post_save.connect(self.post_save_moderation, sender=model)
    
    ## THE FOLLOWING ARE HACKS UNTIL django-comment-utils GETS UPDATED SIGNALS ####
    def pre_save_moderation(self, sender=None, instance=None, **kwargs):
        return super(Moderator, self).pre_save_moderation(sender, instance)

    def post_save_moderation(self, sender=None, instance=None, **kwargs):
        return super(Moderator, self).post_save_moderation(sender, instance)


# Instantiate the ``Moderator`` so that other modules can import and 
# begin to register with it.

moderator = Moderator()
