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

from film20.import_ratings.models import ImportRatings
from film20.import_ratings.models import ImportRatingsLog

class ImportRatingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'kind','submited_at','imported_at','is_imported')
    list_filter = ('kind', 'is_imported')

admin.site.register(ImportRatings, ImportRatingsAdmin)

class ImportRatingsLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at',)
    
admin.site.register(ImportRatingsLog, ImportRatingsLogAdmin)
