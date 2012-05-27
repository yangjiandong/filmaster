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
from film20.blog.models import Blog, Post, PingbackNote
from django.contrib import admin

class BlogAdmin(admin.ModelAdmin):
    list_display        = ('user', 'title',)
    search_fields       = ('user__username','title',)
    raw_id_fields = ['user',]
    
admin.site.register(Blog, BlogAdmin) 

class PostAdmin(admin.ModelAdmin):
    list_display        = ('title', 'publish', 'status','LANG',)
    list_filter         = ('publish', 'status')
    search_fields       = ('title',)
    raw_id_fields = ['user','related_film', 'related_person',]

    def change_view( self, request, object_id, extra_context=None ):
        result = super( PostAdmin, self ).change_view( request, object_id, extra_context )

        if not request.POST.has_key( '_addanother' ) and not request.POST.has_key( '_continue' ):
            next = request.GET.get( 'next', None )
            if next:
                result['Location'] = next

        return result


admin.site.register(Post, PostAdmin)

class PingbackNoteAdmin(admin.ModelAdmin):
    pass

admin.site.register(PingbackNote, PingbackNoteAdmin)
