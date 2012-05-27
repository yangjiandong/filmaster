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
from film20.useractivity.models import UserActivity
from django.contrib import admin
from film20.utils import cache_helper as cache

def make_featured(modeladmin, request, queryset):
    queryset.update(featured=True)
make_featured.short_description = "Mark selected activities as featured"

def make_not_featured(modeladmin, request, queryset):
    queryset.update(featured=False)
    cache_key_name = "main_page_activities_all"
    cache.delete(cache_key_name)

make_not_featured.short_description = "Mark selected activities as not featured"

class UserActivityAdmin(admin.ModelAdmin):
    list_display        = ('user', 'activity_type', 'created_at', 'featured')
    list_filter         = ('activity_type', 'created_at')
    search_fields       = ('activity_type','user',)
    raw_id_fields = ['user', 'post', 'short_review','comment', 'link', 'film', 'person', 
                     'object', 'checkin', 'watching_object', 'related_rating', 'channel', 
                     'demot', 'screening', 'trailer' ]
    actions = [make_featured, make_not_featured]


admin.site.register(UserActivity, UserActivityAdmin)    
