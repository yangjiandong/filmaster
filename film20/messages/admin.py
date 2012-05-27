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
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import User, Group

if "film20.notification" in settings.INSTALLED_APPS:
    from film20.notification import models as notification
else:
    notification = None

from film20.messages.models import Message

class MessageAdminForm(forms.ModelForm):
    """
    Custom AdminForm to enable messages to groups and all users.
    """
    recipient = forms.ModelChoiceField(
        label=_('Recipient'), queryset=User.objects.all(), required=True)

    group = forms.ChoiceField(label=_('group'), required=False,
        help_text=_('Creates the message optionally for all users or a group of users.'))

    def __init__(self, *args, **kwargs):
        super(MessageAdminForm, self).__init__(*args, **kwargs)
        self.fields['group'].choices = self._get_group_choices()

    def _get_group_choices(self):
        return [('', u'---------'), ('all', _('All users'))] + \
            [(group.pk, group.name) for group in Group.objects.all()]

    class Meta:
        model = Message

class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    fieldsets = (
        (None, {
            'fields': (
                'sender',
                ('recipient', 'group'),
            ),
        }),
        (_('Message'), {
            'fields': (
                'parent_msg',
                'subject', 'body',
            ),
            'classes': ('monospace' ),
        }),
    )
    list_display = ('subject', 'sender', 'recipient', 'sent_at', 'read_at')
    list_filter = ('sent_at', 'sender', 'recipient')
    search_fields = ('subject', 'body')

    def save_model(self, request, obj, form, change):
        """
        Saves the message for the recipient and looks in the form instance
        for other possible recipients. Prevents duplication by excludin the
        original recipient from the list of optional recipients.

        When changing an existing message and choosing optional recipients,
        the message is effectively resent to those users.
        """
        obj.save()

        if notification:
            # Getting the appropriate notice labels for the sender and recipients.
            if obj.parent_msg is None:
                sender_label = 'messages_sent'
                recipients_label = 'messages_received'
            else:
                sender_label = 'messages_replied'
                recipients_label = 'messages_reply_received'

            # Notification for the sender.
            notification.send([obj.sender], sender_label, {'message': obj,})

        if form.cleaned_data['group'] == 'all':
            # send to all users
            recipients = User.objects.exclude(pk=obj.recipient.pk)
        else:
            # send to a group of users
            recipients = []
            group = form.cleaned_data['group']
            if group:
                group = Group.objects.get(pk=group)
                recipients.extend(
                    list(group.user_set.exclude(pk=obj.recipient.pk)))
        # create messages for all found recipients
        for user in recipients:
            obj.pk = None
            obj.recipient = user
            obj.save()

            if notification:
                # Notification for the recipient.
                notification.send([user], recipients_label, {'message' : obj,})

admin.site.register(Message, MessageAdmin)
