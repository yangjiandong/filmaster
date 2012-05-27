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
import datetime
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app

from film20.messages.models import Message, Conversation
from film20.messages.forms import ComposeForm
from film20.messages.utils import format_quote
#from django.db import transaction

import logging
logger = logging.getLogger(__name__)

try:
    notification = get_app('notification')
except ImproperlyConfigured:
    notification = None

@login_required
def recent_conversations(request, template_name='messages/recent_conversations.html'):
    """
    Displays a list of received messages for the current user.
    Optional Arguments:
        ``template_name``: name of the template to use.
    """    
    conversation_list = Conversation.objects.user_conversations(request.user, True)
    
    return render(request, template_name, {
        'conversation_list': conversation_list,
    })

@login_required
def sent_messages(request, template_name='messages/sent_messages.html'):
    """
    Displays a list of sent messages by the current user.
    Optional arguments:
        ``template_name``: name of the template to use.
    """
    message_list = Message.objects.outbox_for(request.user)
    return render(request, template_name, {
        'message_list': message_list,
    })

@login_required
def trash(request, template_name='messages/trash.html'):
    """
    Displays a list of deleted messages. 
    Optional arguments:
        ``template_name``: name of the template to use
    Hint: A Cron-Job could periodicly clean up old messages, which are deleted
    by sender and recipient.
    """
    message_list = Message.objects.trash_for(request.user)
    return render(request, template_name, {
        'message_list': message_list,
    })

@login_required
#@transaction.commit_on_success
def compose(request, recipient=None, form_class=ComposeForm,
        template_name='messages/compose.html', success_url=None):
    """
    Displays and handles the ``form_class`` form to compose new messages.
    Required Arguments: None
    Optional Arguments:
        ``recipient``: username of a `django.contrib.auth` User, who should
                       receive the message, optionally multiple usernames
                       could be separated by a '+'
        ``form_class``: the form-class to use
        ``template_name``: the template to use
        ``success_url``: where to redirect after successfull submission
    """
    if request.method == "POST":
        sender = request.user
        form = form_class(request.POST)
        if form.is_valid():
            form.save(sender=request.user)
            request.user.message_set.create(
                message=_(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_inbox')
            return HttpResponseRedirect(success_url)
    else:
        form = form_class()
        if recipient is not None:
            recipients = [u for u in User.objects.filter(username__in=[r.strip() for r in recipient.split('+')])]
            form.fields['recipient'].initial = recipients

    return render(request, template_name, {
        'form': form,
    })

@login_required
#@transaction.commit_on_success
def reply(request, message_id, form_class=ComposeForm,
        template_name='messages/compose.html', success_url=None):
    """
    Prepares the ``form_class`` form for writing a reply to a given message
    (specified via ``message_id``). Uses the ``format_quote`` helper from
    ``messages.utils`` to pre-format the quote.
    """
    parent = get_object_or_404(Message, id=message_id)
    if (parent.sender != request.user) and (parent.recipient != request.user):
        raise Http404
    if request.method == "POST":
        sender = request.user
        form = form_class(request.POST)
        if form.is_valid():
            form.save(sender=request.user, parent_msg=parent)
            request.user.message_set.create(
                message=_(u"Message successfully sent."))
            if success_url is None:
                success_url = reverse('messages_inbox')
            return HttpResponseRedirect(success_url)
    else:
        form = form_class({
            'body': _(u"%(sender)s wrote:\n%(body)s") % {
                'sender': parent.sender, 
                'body': format_quote(parent.body)
                }, 
            'subject': _(u"Re: %(subject)s") % {'subject': parent.subject},
            'recipient': [parent.sender,]
            })
    return render(request, template_name, {
        'form': form,
    })

@login_required
def delete_conversation(request, id):
    if request.POST:
        obj = get_object_or_404(Conversation.objects.user_conversations(request.user), id=id)
        obj.delete()
    return HttpResponseRedirect(reverse(recent_conversations))

@login_required
#@transaction.commit_on_success
def delete(request, message_id, success_url=None):
    """
    Marks a message as deleted by sender or recipient. The message is not
    really removed from the database, because two users must delete a message
    before it's save to remove it completely. 
    A cron-job should prune the database and remove old messages which are 
    deleted by both users.
    As a side effect, this makes it easy to implement a trash with undelete.
    
    You can pass ?next=/foo/bar/ via the url to redirect the user to a different
    page (e.g. `/foo/bar/`) than ``success_url`` after deletion of the message.
    """
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    message.delete_by(user)
    if success_url is None:
        success_url = reverse('messages_inbox')
    if request.GET.has_key('next'):
        success_url = request.GET['next']
    user.message_set.create(message=_(u"Message successfully deleted."))
    if notification:
        notification.send([user], "messages_deleted", {'message': message,})
    return HttpResponseRedirect(success_url)

@login_required
#@transaction.commit_on_success
def undelete(request, message_id, success_url=None):
    """
    Recovers a message from trash. This is achieved by removing the
    ``(sender|recipient)_deleted_at`` from the model.
    """
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    if success_url is None:
        success_url = reverse('messages_inbox')
    if request.GET.has_key('next'):
        success_url = request.GET['next']
    message.undelete_by(user)
    message.save()
    user.message_set.create(message=_(u"Message successfully recovered."))
    if notification:
        notification.send([user], "messages_recovered", {'message': message,})
    return HttpResponseRedirect(success_url)

@login_required
#@transaction.commit_on_success
def view(request, message_id, template_name='messages/view.html'):
    """
    Shows a single message.``message_id`` argument is required.
    The user is only allowed to see the message, if he is either 
    the sender or the recipient. If the user is not allowed a 404
    is raised. 
    If the user is the recipient and the message is unread 
    ``read_at`` is set to the current datetime.
    """
        
    user = request.user
    now = datetime.datetime.now()
    message = get_object_or_404(Message, id=message_id)
    if (message.sender != user) and (message.recipient != user):
        raise Http404
    if message.read_at is None and message.recipient == user:
        message.mark_as_read()
    
    return render(request, template_name, {
        'message': message,
    })

@login_required
def view_conversation(request, id):
    conversation = get_object_or_404(Conversation.objects.user_conversations(request.user), id=id)
    messages = list(conversation.user_messages(request.user))

    for i in (0, -3, -2, -1):
        try:
            messages[i].visible = True    
        except IndexError, e:
            pass

    if not conversation.is_read():
        logger.info("%r %r %r", conversation.user, conversation.sender_unread_cnt, conversation.recipient_unread_cnt)
        conversation.mark_read()
        conversation.save()

    return render(request, "messages/single_conversation.html", {
        'conversation_messages': messages,
        'conversation': conversation,        
    })
