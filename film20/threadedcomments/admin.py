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
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from models import ThreadedComment, FreeThreadedComment

def delete(modeladmin, request, queryset):
    for element in queryset:
        element.delete()

class ThreadedCommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('content_type', 'object_id')}),
        (_('Parent'), {'fields' : ('parent',)}),
        (_('Content'), {'fields': ('user', 'comment')}),
        (_('Meta'), {'fields': ('is_public', 'date_submitted', 'date_modified', 'date_approved', 'is_approved', 'ip_address')}),
    )
    list_display = ('user', 'date_submitted', 'content_type', 'get_content_object', 'parent', '__unicode__')
    list_filter = ('date_submitted',)
    date_hierarchy = 'date_submitted'
    search_fields = ('comment', 'user__username')
    raw_id_fields = ['parent','content_type','user']
    actions = [delete]
    
class FreeThreadedCommentAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('content_type', 'object_id')}),
        (_('Parent'), {'fields' : ('parent',)}),
        (_('Content'), {'fields': ('name', 'website', 'email', 'comment')}),
        (_('Meta'), {'fields': ('date_submitted', 'date_modified', 'date_approved', 'is_public', 'ip_address', 'is_approved')}),
    )
    list_display = ('name', 'date_submitted', 'content_type', 'get_content_object', 'parent', '__unicode__')
    list_filter = ('date_submitted',)
    date_hierarchy = 'date_submitted'
    search_fields = ('comment', 'name', 'email', 'website')


admin.site.register(ThreadedComment, ThreadedCommentAdmin)
admin.site.register(FreeThreadedComment, FreeThreadedCommentAdmin)
