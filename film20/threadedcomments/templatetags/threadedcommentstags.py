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
import re
from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from film20.utils.cache_helper import *
from film20.utils import cache_helper as cache
from film20.threadedcomments.models import ThreadedComment, FreeThreadedComment
from film20.threadedcomments.forms import ThreadedCommentForm, FreeThreadedCommentForm
import logging

logger = logging.getLogger(__name__)

# Regular expressions for getting rid of newlines and witespace
inbetween = re.compile('>[ \r\n]+<')
newlines = re.compile('\r|\n')
register = template.Library()

def get_contenttype_kwargs(content_object):
    """
    Gets the basic kwargs necessary for almost all of the following tags.
    """
    kwargs = {
        'content_type' : ContentType.objects.get_for_model(content_object).id,
        'object_id' : getattr(content_object, 'pk', getattr(content_object, 'id')),
    }
    return kwargs

def get_comment_url(content_object, parent=None):
    """
    Given an object and an optional parent, this tag gets the URL to POST to for the
    creation of new ``ThreadedComment`` objects.
    """
    kwargs = get_contenttype_kwargs(content_object)
    if parent:
        if not isinstance(parent, ThreadedComment):
            raise template.TemplateSyntaxError, "get_comment_url requires its parent object to be of type ThreadedComment"
        kwargs.update({'parent_id' : getattr(parent, 'pk', getattr(parent, 'id'))})
        return reverse('tc_comment_parent', kwargs=kwargs)
    else:
        return reverse('tc_comment', kwargs=kwargs)

def get_contenttype_kwargs_planet(content_object, content_object_id):
    """
    Gets the basic kwargs necessary for almost all of the following tags.
    adz: use content_object_id to avoid queries to objects tables
    """
    kwargs = {
        'content_type' : ContentType.objects.get_for_model(content_object).id,
        'object_id' : content_object_id,
    }
    return kwargs

def get_comment_url_planet(content_object, content_object_id, parent=None):
    """
    Given an object and an optional parent, this tag gets the URL to POST to for the
    creation of new ``ThreadedComment`` objects.
    adz: to get kwargs call new function get_contenttype_kwargs_planet
    """
    #kwargs = get_contenttype_kwargs_planet(content_object, content_object_id)
    content_type = ContentType.objects.get_for_model(content_object.post).id
    if parent:
        if not isinstance(parent, ThreadedComment):
            raise template.TemplateSyntaxError, "get_comment_url requires its parent object to be of type ThreadedComment"
        kwargs.update({'parent_id' : getattr(parent, 'pk', getattr(parent, 'id'))})
        return reverse('tc_comment_parent', kwargs=kwargs)
    else:
        return '^comment/'+str(content_type)+'/'+str(content_object_id)+'/'

def get_comment_url_ajax(content_object, parent=None, ajax_type='json'):
    """
    Given an object and an optional parent, this tag gets the URL to POST to for the
    creation of new ``ThreadedComment`` objects.  It returns the latest created object
    in the AJAX form of the user's choosing (json or xml).
    """
    kwargs = get_contenttype_kwargs(content_object)
    kwargs.update({'ajax' : ajax_type})
    if parent:
        if not isinstance(parent, ThreadedComment):
            raise template.TemplateSyntaxError, "get_comment_url_ajax requires its parent object to be of type ThreadedComment"
        kwargs.update({'parent_id' : getattr(parent, 'pk', getattr(parent, 'id'))})
        return reverse('tc_comment_parent_ajax', kwargs=kwargs)
    else:
        return reverse('tc_comment_ajax', kwargs=kwargs)

def get_comment_url_json(content_object, parent=None):
    """
    Wraps ``get_comment_url_ajax`` with ``ajax_type='json'``
    """
    try:
        return get_comment_url_ajax(content_object, parent, ajax_type="json")
    except template.TemplateSyntaxError:
        raise template.TemplateSyntaxError, "get_comment_url_json requires its parent object to be of type ThreadedComment"
    return ''

def get_comment_url_xml(content_object, parent=None):
    """
    Wraps ``get_comment_url_ajax`` with ``ajax_type='xml'``
    """
    try:
        return get_comment_url_ajax(content_object, parent, ajax_type="xml")
    except template.TemplateSyntaxError:
        raise template.TemplateSyntaxError, "get_comment_url_xml requires its parent object to be of type ThreadedComment"
    return ''

def get_free_comment_url(content_object, parent=None):
    """
    Given an object and an optional parent, this tag gets the URL to POST to for the
    creation of new ``FreeThreadedComment`` objects.
    """
    kwargs = get_contenttype_kwargs(content_object)
    if parent:
        if not isinstance(parent, FreeThreadedComment):
            raise template.TemplateSyntaxError, "get_free_comment_url requires its parent object to be of type FreeThreadedComment"
        kwargs.update({'parent_id' : getattr(parent, 'pk', getattr(parent, 'id'))})
        return reverse('tc_free_comment_parent', kwargs=kwargs)
    else:
        return reverse('tc_free_comment', kwargs=kwargs)

def get_free_comment_url_ajax(content_object, parent=None, ajax_type='json'):
    """
    Given an object and an optional parent, this tag gets the URL to POST to for the
    creation of new ``FreeThreadedComment`` objects.  It returns the latest created object
    in the AJAX form of the user's choosing (json or xml).
    """
    kwargs = get_contenttype_kwargs(content_object)
    kwargs.update({'ajax' : ajax_type})
    if parent:
        if not isinstance(parent, FreeThreadedComment):
            raise template.TemplateSyntaxError, "get_free_comment_url_ajax requires its parent object to be of type FreeThreadedComment"
        kwargs.update({'parent_id' : getattr(parent, 'pk', getattr(parent, 'id'))})
        return reverse('tc_free_comment_parent_ajax', kwargs=kwargs)
    else:
        return reverse('tc_free_comment_ajax', kwargs=kwargs)

def get_free_comment_url_json(content_object, parent=None):
    """
    Wraps ``get_free_comment_url_ajax`` with ``ajax_type='json'``
    """
    try:
        return get_free_comment_url_ajax(content_object, parent, ajax_type="json")
    except template.TemplateSyntaxError:
        raise template.TemplateSyntaxError, "get_free_comment_url_json requires its parent object to be of type FreeThreadedComment"
    return ''

def get_free_comment_url_xml(content_object, parent=None):
    """
    Wraps ``get_free_comment_url_ajax`` with ``ajax_type='xml'``
    """
    try:
        return get_free_comment_url_ajax(content_object, parent, ajax_type="xml")
    except template.TemplateSyntaxError:
        raise template.TemplateSyntaxError, "get_free_comment_url_xml requires its parent object to be of type FreeThreadedComment"
    return ''

def auto_transform_markup(comment):
    """
    Given a comment (``ThreadedComment`` or ``FreeThreadedComment``), this tag
    looks up the markup type of the comment and formats the output accordingly.
    
    It can also output the formatted content to a context variable, if a context name is
    specified.
    """
    try:
        from django.utils.html import escape
        from threadedcomments.models import MARKDOWN, TEXTILE, REST, PLAINTEXT
        if comment.markup == MARKDOWN:
            from django.contrib.markup.templatetags.markup import markdown
            return markdown(comment.comment)
        elif comment.markup == TEXTILE:
            from django.contrib.markup.templatetags.markup import textile
            return textile(comment.comment)
        elif comment.markup == REST:
            from django.contrib.markup.templatetags.markup import restructuredtext
            return restructuredtext(comment.comment)
#        elif comment.markup == HTML:
#            return mark_safe(force_unicode(comment.comment))
        elif comment.markup == PLAINTEXT:
            return escape(comment.comment)
    except ImportError:
        # Not marking safe, in case tag fails and users input malicious code.
        return force_unicode(comment.comment)

def do_auto_transform_markup(parser, token):
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag must be of format {%% %r COMMENT %%} or of format {%% %r COMMENT as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0], token.contents.split()[0])
    if len(split) == 2:
        return AutoTransformMarkupNode(split[1])
    elif len(split) == 4:
        return AutoTransformMarkupNode(split[1], context_name=split[3])
    else:
        raise template.TemplateSyntaxError, "Invalid number of arguments for tag %r" % split[0]

class AutoTransformMarkupNode(template.Node):
    def __init__(self, comment, context_name=None):
        self.comment = template.Variable(comment)
        self.context_name = context_name
    def render(self, context):
        comment = self.comment.resolve(context)
        if self.context_name:
            context[self.context_name] = auto_transform_markup(comment)
            return ''
        else:
            return auto_transform_markup(comment)

def do_get_threaded_comment_tree(parser, token):
    """
    Gets a tree (list of objects ordered by preorder tree traversal, and with an
    additional ``depth`` integer attribute annotated onto each ``ThreadedComment``.
    """
    error_string = "%r tag must be of format {%% get_threaded_comment_tree for OBJECT [TREE_ROOT] as CONTEXT_VARIABLE %%}" % token.contents.split()[0]
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(split) == 5:
        return CommentTreeNode(split[2], split[4], split[3])
    elif len(split) == 6:
        return CommentTreeNode(split[2], split[5], split[3])
    else:
        raise template.TemplateSyntaxError(error_string)

def do_get_free_threaded_comment_tree(parser, token):
    """
    Gets a tree (list of objects ordered by traversing tree in preorder, and with an
    additional ``depth`` integer attribute annotated onto each ``FreeThreadedComment.``
    """
    error_string = "%r tag must be of format {%% get_free_threaded_comment_tree for OBJECT [TREE_ROOT] as CONTEXT_VARIABLE %%}" % token.contents.split()[0]
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(split) == 5:
        return FreeCommentTreeNode(split[2], split[4], split[3])
    elif len(split) == 6:
        return FreeCommentTreeNode(split[2], split[5], split[3])
    else:
        raise template.TemplateSyntaxError(error_string)

class CommentTreeNode(template.Node):
    def __init__(self, content_object, context_name, tree_root):
        self.content_object = template.Variable(content_object)
        self.tree_root = template.Variable(tree_root)
        self.tree_root_str = tree_root
        self.context_name = context_name
    def render(self, context):
        content_object = self.content_object.resolve(context)
        try:
            tree_root = self.tree_root.resolve(context)
        except template.VariableDoesNotExist:
            if self.tree_root_str == 'as':
                tree_root = None
            else:
                try:
                    tree_root = int(self.tree_root_str)
                except ValueError:
                    tree_root = self.tree_root_str
        context[self.context_name] = ThreadedComment.public.get_tree(content_object, root=tree_root)
        return ''

class FreeCommentTreeNode(template.Node):
    def __init__(self, content_object, context_name, tree_root):
        self.content_object = template.Variable(content_object)
        self.tree_root = template.Variable(tree_root)
        self.tree_root_str = tree_root
        self.context_name = context_name
    def render(self, context):
        content_object = self.content_object.resolve(context)
        try:
            tree_root = self.tree_root.resolve(context)
        except template.VariableDoesNotExist:
            if self.tree_root_str == 'as':
                tree_root = None
            else:
                try:
                    tree_root = int(self.tree_root_str)
                except ValueError:
                    tree_root = self.tree_root_str
        context[self.context_name] = FreeThreadedComment.public.get_tree(content_object, root=tree_root)
        return ''

def do_get_comment_count(parser, token):
    """
    Gets a count of how many ThreadedComment objects are attached to the given
    object.
    """
    error_message = "%r tag must be of format {%% %r for OBJECT as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if split[1] != 'for' or split[3] != 'as':
        raise template.TemplateSyntaxError, error_message
    return ThreadedCommentCountNode(split[2], split[4])

class ThreadedCommentCountNode(template.Node):
    def __init__(self, content_object, context_name):
        self.content_object = template.Variable(content_object)
        self.context_name = context_name
    def render(self, context):
        content_object = self.content_object.resolve(context)
        context[self.context_name] = ThreadedComment.public.all_for_object(content_object).count()
        return ''
        
def do_get_free_comment_count(parser, token):
    """
    Gets a count of how many FreeThreadedComment objects are attached to the 
    given object.
    """
    error_message = "%r tag must be of format {%% %r for OBJECT as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if split[1] != 'for' or split[3] != 'as':
        raise template.TemplateSyntaxError, error_message
    return FreeThreadedCommentCountNode(split[2], split[4])

class FreeThreadedCommentCountNode(template.Node):
    def __init__(self, content_object, context_name):
        self.content_object = template.Variable(content_object)
        self.context_name = context_name
    def render(self, context):
        content_object = self.content_object.resolve(context)
        context[self.context_name] = FreeThreadedComment.public.all_for_object(content_object).count()
        return ''

def oneline(value):
    """
    Takes some HTML and gets rid of newlines and spaces between tags, rendering
    the result all on one line.
    """
    try:
        return mark_safe(newlines.sub('', inbetween.sub('><', value)))
    except:
        return value

def do_get_threaded_comment_form(parser, token):
    """
    Gets a FreeThreadedCommentForm and inserts it into the context.
    """
    error_message = "%r tag must be of format {%% %r as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if split[1] != 'as':
        raise template.TemplateSyntaxError, error_message
    if len(split) != 3:
        raise template.TemplateSyntaxError, error_message
    if "free" in split[0]:
        is_free = True
    else:
        is_free = False
    return ThreadedCommentFormNode(split[2], free=is_free)

class ThreadedCommentFormNode(template.Node):
    def __init__(self, context_name, free=False):
        self.context_name = context_name
        self.free = free
    def render(self, context):
        if self.free:
            form = FreeThreadedCommentForm()
        else:
            form = ThreadedCommentForm()
        context[self.context_name] = form
        return ''

def do_get_latest_comments(parser, token):
    """
    Gets the latest comments by date_submitted.
    """
    error_message = "%r tag must be of format {%% %r NUM_TO_GET as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 4:
        raise template.TemplateSyntaxError, error_message
    if split[2] != 'as':
        raise template.TemplateSyntaxError, error_message
    if "free" in split[0]:
        is_free = True
    else:
        is_free = False
    return LatestCommentsNode(split[1], split[3], free=is_free)

class LatestCommentsNode(template.Node):
    def __init__(self, num, context_name, free=False):
        self.num = num
        self.context_name = context_name
        self.free = free
    def render(self, context):
        if self.free:
            comments = FreeThreadedComment.objects.order_by('-date_submitted')[:self.num]
        else:
            comments = ThreadedComment.objects.select_related().order_by('-date_submitted')[:self.num]
        context[self.context_name] = comments
        return ''

def do_get_user_comments(parser, token):
    """
    Gets all comments submitted by a particular user.
    """
    error_message = "%r tag must be of format {%% %r for OBJECT as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 5:
        raise template.TemplateSyntaxError, error_message
    return UserCommentsNode(split[2], split[4])

class UserCommentsNode(template.Node):
    def __init__(self, user, context_name):
        self.user = template.Variable(user)
        self.context_name = context_name
    def render(self, context):
        user = self.user.resolve(context)
        context[self.context_name] = user.threadedcomment_set.all()
        return ''

def do_get_user_comment_count(parser, token):
    """
    Gets the count of all comments submitted by a particular user.
    """
    error_message = "%r tag must be of format {%% %r for OBJECT as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 5:
        raise template.TemplateSyntaxError, error_message
    return UserCommentCountNode(split[2], split[4])

class UserCommentCountNode(template.Node):
    def __init__(self, user, context_name):
        self.user = template.Variable(user)
        self.context_name = context_name
    def render(self, context):
        user = self.user.resolve(context)
        context[self.context_name] = user.threadedcomment_set.all().count()
        return ''

@register.tag
def get_all_comments(parser, token):
    """
        Gets all comments for object
    """

    error_message = "Error in get_all_comments tag"
    misuse_message = "Inappropriate use of tag get_all_comments"
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 4:
        raise template.TemplateSyntaxError, misuse_message

    return GetAllCommentsNode(split[1], split[3])

class GetAllCommentsNode(template.Node):
    def __init__(self, object, context_name):
        self.object = template.Variable(object)
        self.context_name = context_name

    def render(self, context):
        key = cache.Key("all-comments-tag", self.object.resolve(context))
        query = cache.get(key)
        if query is None:
            query = ThreadedComment.objects.select_related().\
                    filter(object_id=self.object.resolve(context),
                           status=ThreadedComment.PUBLIC_STATUS).\
                    order_by('date_submitted')
            cache.set(key, query)
            context[self.context_name] = query
            return ''
        else:
            context[self.context_name] = query
            return ''

def do_get_oldest_comments(parser, token):
    """
    Gets oldest comments for object.
    """
    error_message = "error!"
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if len(split) != 5:
        raise template.TemplateSyntaxError, error_message
    return GetOldestCommentsNode(split[1], split[2], split[4])

class GetOldestCommentsNode(template.Node):
    def __init__(self, object, count, context_name):
        self.object = template.Variable(object)

        self.count = int(count)
        self.context_name = context_name
    
    def render(self, context):
        key = "oldest-comments-tag-%s" % self.object.resolve(context)
        logger.debug("oldest-comments-tag key %s" % key)
        query = get_cache(CACHE_COMMENTS, key)
        if query is None:
            logger.debug("oldest-comments-tag MISS")
            query = ThreadedComment.objects.select_related().filter(object_id=self.object.resolve(context),status=ThreadedComment.PUBLIC_STATUS).order_by('date_submitted')[:self.count]
            set_cache(CACHE_COMMENTS, key, query)
            context[self.context_name] = query
            return ''
        else:
            context[self.context_name] = query
            logger.debug("oldest-comments-tag HIT") 
            return ''

register.simple_tag(get_comment_url)
register.simple_tag(get_comment_url_planet)
register.simple_tag(get_comment_url_json)
register.simple_tag(get_comment_url_xml)
register.simple_tag(get_free_comment_url)
register.simple_tag(get_free_comment_url_json)
register.simple_tag(get_free_comment_url_xml)
#register.simple_tag(get_oldest_comments)

register.filter('oneline', oneline)

register.tag('auto_transform_markup', do_auto_transform_markup)
register.tag('get_threaded_comment_tree', do_get_threaded_comment_tree)
register.tag('get_free_threaded_comment_tree', do_get_free_threaded_comment_tree)
register.tag('get_comment_count', do_get_comment_count)
register.tag('get_free_comment_count', do_get_free_comment_count)
register.tag('get_free_threaded_comment_form', do_get_threaded_comment_form)
register.tag('get_threaded_comment_form', do_get_threaded_comment_form)
register.tag('get_latest_comments', do_get_latest_comments)
register.tag('get_oldest_comments', do_get_oldest_comments)
register.tag('get_latest_free_comments', do_get_latest_comments)
register.tag('get_user_comments', do_get_user_comments)
register.tag('get_user_comment_count', do_get_user_comment_count)
