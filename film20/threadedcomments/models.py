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
from datetime import timedelta, datetime

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.encoding import force_unicode

from film20.utils.cache_helper import *
from film20.core.models import Object, Profile
LANGUAGE_CODE = settings.LANGUAGE_CODE

import logging
logger = logging.getLogger(__name__)

DEFAULT_MAX_COMMENT_LENGTH = getattr(settings, 'DEFAULT_MAX_COMMENT_LENGTH', 50000)
DEFAULT_MAX_COMMENT_DEPTH = getattr(settings, 'DEFAULT_MAX_COMMENT_DEPTH', 8)

MARKDOWN = 1
TEXTILE = 2
REST = 3
#HTML = 4
PLAINTEXT = 5
MARKUP_CHOICES = (
    (MARKDOWN, _("markdown")),
    (TEXTILE, _("textile")),
    (REST, _("restructuredtext")),
#    (HTML, _("html")),
    (PLAINTEXT, _("plaintext")),
)

DEFAULT_MARKUP = getattr(settings, 'DEFAULT_MARKUP', PLAINTEXT)
DUPLICATE_COMMENT_MINUTES = getattr(settings, "DUPLICATE_COMMENT_MINUTES", 5)

def dfs(node, all_nodes, depth):
    """
    Performs a recursive depth-first search starting at ``node``.  This function
    also annotates an attribute, ``depth``, which is an integer that represents
    how deeply nested this node is away from the original object.
    """
    node.depth = depth
    to_return = [node,]
    for subnode in all_nodes:
        if subnode.parent and subnode.parent.id == node.id:
            to_return.extend(dfs(subnode, all_nodes, depth+1))
    return to_return

class ThreadedCommentManager(models.Manager):
    """
    A ``Manager`` which will be attached to each comment model.  It helps to facilitate
    the retrieval of comments in tree form and also has utility methods for
    creating and retrieving objects related to a specific content object.
    """
    def get_query_set(self):
        return super(ThreadedCommentManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)   
    
    def get_tree(self, content_object, root=None):
        """
        Runs a depth-first search on all comments related to the given content_object.
        This depth-first search adds a ``depth`` attribute to the comment which
        signifies how how deeply nested the comment is away from the original object.
        
        If root is specified, it will start the tree from that comment's ID.
        
        Ideally, one would use this ``depth`` attribute in the display of the comment to
        offset that comment by some specified length.
        
        The following is a (VERY) simple example of how the depth property might be used in a template:
        
            {% for comment in comment_tree %}
                <p style="margin-left: {{ comment.depth }}em">{{ comment.comment }}</p>
            {% endfor %}
        """
        content_type = ContentType.objects.get_for_model(content_object)
        children = list(self.get_query_set().select_related().filter(
            LANG=LANGUAGE_CODE,
            status = ThreadedComment.PUBLIC_STATUS,
            content_type = content_type,
            object_id = getattr(content_object, 'pk', getattr(content_object, 'id')),
        ).select_related().order_by('date_submitted'))
        to_return = []
        if root:
            if isinstance(root, int):
                root_id = root
            else:
                root_id = root.id
            to_return = [c for c in children if c.id == root_id]
            if to_return:
                to_return[0].depth = 0
                for child in children:
                    if child.parent_id == root_id:
                        to_return.extend(dfs(child, children, 1))
        else:
            for child in children:
                if not child.parent:
                    to_return.extend(dfs(child, children, 0))
        return to_return

    def _generate_object_kwarg_dict(self, content_object, **kwargs):
        """
        Generates the most comment keyword arguments for a given ``content_object``.
        """
        kwargs['content_type'] = ContentType.objects.get_for_model(content_object)
        kwargs['object_id'] = getattr(content_object, 'pk', getattr(content_object, 'id'))
        return kwargs

    def create_for_object(self, content_object, **kwargs):
        """
        A simple wrapper around ``create`` for a given ``content_object``.
        """
        return self.create(**self._generate_object_kwarg_dict(content_object, **kwargs))
    
    def get_or_create_for_object(self, content_object, **kwargs):
        """
        A simple wrapper around ``get_or_create`` for a given ``content_object``.
        """
        return self.get_or_create(**self._generate_object_kwarg_dict(content_object, **kwargs))
    
    def get_for_object(self, content_object, **kwargs):
        """
        A simple wrapper around ``get`` for a given ``content_object``.
        """
        return self.get(**self._generate_object_kwarg_dict(content_object, **kwargs))

    def all_for_object(self, content_object, **kwargs):
        """
        Prepopulates a QuerySet with all comments related to the given ``content_object``.
        """
        return self.filter(**self._generate_object_kwarg_dict(content_object, **kwargs))

    def delete_for_object(self, content_object):
        """
        Marks comments as deleted for given object
        """
        comments = self.filter(object_id=content_object)
        for comment in comments:
            comment.status = Object.DELETED_STATUS
            comment.save()
        return comments

class PublicThreadedCommentManager(ThreadedCommentManager):
    """
    A ``Manager`` which borrows all of the same methods from ``ThreadedCommentManager``,
    but which also restricts the queryset to only the published methods 
    (in other words, ``is_public = True``).
    """
    def get_query_set(self):
        return super(ThreadedCommentManager, self).get_query_set().filter(
            ( Q(is_public = True) | Q(is_approved = True) ) & Q(parent_object__status = Object.PUBLIC_STATUS )
        )

class ThreadedComment(Object):
    """
    A threaded comment which must be associated with an instance of 
    ``django.contrib.auth.models.User``.  It is given its hierarchy by
    a nullable relationship back on itself named ``parent``.
    
    This ``ThreadedComment`` supports several kinds of markup languages,
    including Textile, Markdown, and ReST.
    
    It also includes two Managers: ``objects``, which is the same as the normal
    ``objects`` Manager with a few added utility functions (see above), and
    ``public``, which has those same utility functions but limits the QuerySet to
    only those values which are designated as public (``is_public=True``).
    """
    # Generic Foreign Key Fields
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(_('object ID'))
    content_object = generic.GenericForeignKey()
    
    # Hierarchy Field
    parent = models.ForeignKey('self', null=True, blank=True, default=None, related_name='children')
    
    parent_object = models.OneToOneField(Object, parent_link=True)
    # User Field
    user = models.ForeignKey(User)
    
    # Date Fields
    date_submitted = models.DateTimeField(_('date/time submitted'), default = datetime.now)
    date_modified = models.DateTimeField(_('date/time modified'), default = datetime.now)
    date_approved = models.DateTimeField(_('date/time approved'), default=None, null=True, blank=True)
    
    # Meat n' Potatoes
    comment = models.TextField(_('comment'))
    markup = models.IntegerField(choices=MARKUP_CHOICES, default=DEFAULT_MARKUP, null=True, blank=True)
    
    # Status Fields
    is_public = models.BooleanField(_('is public'), default = True)
    is_approved = models.BooleanField(_('is approved'), default = False)
    
    # Extra Field
    ip_address = models.IPAddressField(_('IP address'), null=True, blank=True)
    
    objects = ThreadedCommentManager()
    all_objects = models.Manager()
    public = PublicThreadedCommentManager()
    
    # LANG adz
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    is_first_post = models.BooleanField(_('is first post in thread'), default=False)
    def __unicode__(self):
        if len(self.comment) > 50:
            return self.comment[:50] + "..."
        return self.comment[:50]

    def update_number_of_comments(self, n):
        model_class = ContentType.objects.get_for_id(self.content_type_id).model_class()
        if 'number_of_comments' in model_class._meta.get_all_field_names():
            model_class.objects.filter(id=self.object_id).update(number_of_comments=F('number_of_comments') + n)

    def delete(self, **kwargs):
        self.update_number_of_comments(-1)
        super(ThreadedComment, self).delete(**kwargs)

    def get_absolute_url(self):
        if self.content_object is None:
            return None
        return self.content_object.get_absolute_url() + "#" + str(self.id)

    def get_absolute_url_old_style(self):
        if self.content_object is None:
            return None
        return self.content_object.get_absolute_url_old_style() + "#" + str(self.id)

    def get_slug(self):
        if self.content_object is None:
            return None
        return self.content_object.get_slug() + "#" + str(self.id)

    def get_comment_title(self):
        return self.content_object.get_comment_title() if self.content_object else None

    def get_title(self):
        return self.content_object.get_title() if self.content_object else None

    def save(self, **kwargs):
        if not self.content_object:
            raise Exception("ThreadedComment.save: content_object missing"
                            "for new comment")

        if self.ip_address == "":
            self.ip_address = "0.0.0.0"
        self.update_number_of_comments(1)
        if not self.markup:
            self.markup = DEFAULT_MARKUP
        self.date_modified = datetime.now()
        if not self.date_approved and self.is_approved:
            self.date_approved = datetime.now()
        super(ThreadedComment, self).save(**kwargs)
        if getattr(self, '_save_activity', True):
            key = "oldest-comments-tag-%s" % self.content_object.id
            logger.debug("delete cache oldest-comments-tag-%s" % self.content_object.id)
            delete_cache(CACHE_COMMENTS, key)
            self.save_activity()

    def save_activity(self):
        """
            Save new activity, if activity exists updates it
        """
        from film20.useractivity.models import UserActivity

        if not self.content_object:
            raise Exception("ThreadedComment.save_activity: content_object"
                            "missing for new commment")
        
        try:
            # Checking if activity already exists for given note, if so update activity            
            act = UserActivity.objects.get(activity_type = UserActivity.TYPE_COMMENT, comment = self, user = self.user)
            act.content = self.comment
            act.title = self.content_object.get_comment_title()
            act.username = self.user.username
            act.is_first_post = self.is_first_post
            act.status = self.status
            if settings.ENSURE_OLD_STYLE_PERMALINKS:
                act.permalink = self.content_object.get_absolute_url_old_style() + "#" + str(self.id)
            else:
                act.permalink = self.content_object.get_absolute_url() + "#" + str(self.id)
            act.slug = self.content_object.get_slug() + "#" + str(self.id)
            act.save()
        except UserActivity.DoesNotExist:
            # Activity does not exist - create a new one 
            act = UserActivity()
            act.user = self.user
            act.username = self.user.username
            act.activity_type = UserActivity.TYPE_COMMENT
            act.comment = self
            # title for object related with comment
            act.title = self.content_object.get_comment_title()
            act.content = self.comment
            act.is_first_post = self.is_first_post
            act.status = self.status
            if settings.ENSURE_OLD_STYLE_PERMALINKS:
                act.permalink = self.content_object.get_absolute_url_old_style() + "#" + str(self.id)
            else:
                act.permalink = self.content_object.get_absolute_url() + "#" + str(self.id)
            act.slug = self.content_object.get_slug() + "#" + str(self.id)
            act.save()

    def get_content_object(self):
        """
        Wrapper around the GenericForeignKey due to compatibility reasons
        and due to ``list_display`` limitations.
        """
        return self.content_object

    def get_children(self):
        """
           Return child for comment
        """
        return ThreadedComment.objects.filter(parent=self.id)

    def get_parent(self):
        """
           return parent comment for given comment
        """
        if self.parent:
            try:
                return ThreadedComment.objects.get(id=self.parent.id)
            except ThreadedComment.DoesNotExist:
                return False
        else:
            return False

    def get_base_data(self, show_dates=True):
        """
        Outputs a Python dictionary representing the most useful bits of
        information about this particular object instance.
        
        This is mostly useful for testing purposes, as the output from the
        serializer changes from run to run.  However, this may end up being
        useful for JSON and/or XML data exchange going forward and as the
        serializer system is changed.
        """
        markup = "plaintext"
        for markup_choice in MARKUP_CHOICES:
            if self.markup == markup_choice[0]:
                markup = markup_choice[1]
                break
        to_return = {
            'content_object' : self.content_object,
            'parent' : self.parent,
            'user' : self.user,
            'comment' : self.comment,
            'is_public' : self.is_public,
            'is_approved' : self.is_approved,
            'ip_address' : self.ip_address,
            'markup' : force_unicode(markup),
        }
        if show_dates:
            to_return['date_submitted'] = self.date_submitted
            to_return['date_modified'] = self.date_modified
            to_return['date_approved'] = self.date_approved
        return to_return
    
    class Meta:
        ordering = ('-date_submitted',)
        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        get_latest_by = "date_submitted"

    
class FreeThreadedComment(models.Model):
    """
    A threaded comment which need not be associated with an instance of 
    ``django.contrib.auth.models.User``.  Instead, it requires minimally a name,
    and maximally a name, website, and e-mail address.  It is given its hierarchy
    by a nullable relationship back on itself named ``parent``.
    
    This ``FreeThreadedComment`` supports several kinds of markup languages,
    including Textile, Markdown, and ReST.
    
    It also includes two Managers: ``objects``, which is the same as the normal
    ``objects`` Manager with a few added utility functions (see above), and
    ``public``, which has those same utility functions but limits the QuerySet to
    only those values which are designated as public (``is_public=True``).
    """
    # Generic Foreign Key Fields
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(_('object ID'))
    content_object = generic.GenericForeignKey()
    
    # Hierarchy Field
    parent = models.ForeignKey('self', null = True, blank=True, default = None, related_name='children')
    
    # User-Replacement Fields
    name = models.CharField(_('name'), max_length = 128)
    website = models.URLField(_('site'), blank = True)
    email = models.EmailField(_('e-mail address'), blank = True)
    
    # Date Fields
    date_submitted = models.DateTimeField(_('date/time submitted'), default = datetime.now)
    date_modified = models.DateTimeField(_('date/time modified'), default = datetime.now)
    date_approved = models.DateTimeField(_('date/time approved'), default=None, null=True, blank=True)
    
    # Meat n' Potatoes
    comment = models.TextField(_('comment'))
    markup = models.IntegerField(choices=MARKUP_CHOICES, default=DEFAULT_MARKUP, null=True, blank=True)
    
    # Status Fields
    is_public = models.BooleanField(_('is public'), default = True)
    is_approved = models.BooleanField(_('is approved'), default = False)
    
    # Extra Field
    ip_address = models.IPAddressField(_('IP address'), null=True, blank=True)
    
    objects = ThreadedCommentManager()
    public = PublicThreadedCommentManager()
    # LANG adz
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
        
    def __unicode__(self):
        if len(self.comment) > 50:
            return self.comment[:50] + "..."
        return self.comment[:50]
    
    def save(self, **kwargs):
        if not self.markup:
            self.markup = DEFAULT_MARKUP
        self.date_modified = datetime.now()
        if not self.date_approved and self.is_approved:
            self.date_approved = datetime.now()
        super(FreeThreadedComment, self).save()
    
    def get_content_object(self, **kwargs):
        """
        Wrapper around the GenericForeignKey due to compatibility reasons
        and due to ``list_display`` limitations.
        """
        return self.content_object
    
    def get_base_data(self, show_dates=True):
        """
        Outputs a Python dictionary representing the most useful bits of
        information about this particular object instance.
        
        This is mostly useful for testing purposes, as the output from the
        serializer changes from run to run.  However, this may end up being
        useful for JSON and/or XML data exchange going forward and as the
        serializer system is changed.
        """
        markup = "plaintext"
        for markup_choice in MARKUP_CHOICES:
            if self.markup == markup_choice[0]:
                markup = markup_choice[1]
                break
        to_return = {
            'content_object' : self.content_object,
            'parent' : self.parent,
            'name' : self.name,
            'website' : self.website,
            'email' : self.email,
            'comment' : self.comment,
            'is_public' : self.is_public,
            'is_approved' : self.is_approved,
            'ip_address' : self.ip_address,
            'markup' : force_unicode(markup),
        }
        if show_dates:
            to_return['date_submitted'] = self.date_submitted
            to_return['date_modified'] = self.date_modified
            to_return['date_approved'] = self.date_approved
        return to_return
    
    class Meta:
        ordering = ('-date_submitted',)
        verbose_name = _("Free Threaded Comment")
        verbose_name_plural = _("Free Threaded Comments")
        get_latest_by = "date_submitted"

class TestModel(models.Model):
    """
    This model is simply used by this application's test suite as a model to 
    which to attach comments.
    """
    name = models.CharField(max_length=5)
    is_public = models.BooleanField(default=True)
    date = models.DateTimeField(default=datetime.now)


#TODO: add user id to the check. The problem with that is that there is no user ID in comments form
def check_duplicate_comment(comment_text):
    """
        Returns True is the exact same comment text has been submitted during last
        X minutes (configurable on settings level)
    """
    now = datetime.today()
    five_minutes_ago = now - timedelta(minutes=DUPLICATE_COMMENT_MINUTES)
    try:
        ThreadedComment.objects.get(comment=comment_text, date_submitted__gte=five_minutes_ago)
    except ThreadedComment.DoesNotExist:
        # doesn't exist = unique comment
        return False
    except ThreadedComment.MultipleObjectsReturned:
        pass
    return True
