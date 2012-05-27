from django.contrib import admin
from film20.import_films.models import FilmToImport
from film20.import_films.models import ImportedFilm

class FilmToImportAdmin(admin.ModelAdmin):
    list_display = ('title','user','created_at','is_imported','status','attempts')
    list_filter = ('is_imported','status')
    raw_id_fields = ['user']

admin.site.register(FilmToImport, FilmToImportAdmin)

class ImportedFilmAdmin(admin.ModelAdmin):
    list_display = ('film','user','created_at',)
    raw_id_fields = ['film','user']
    
admin.site.register(ImportedFilm, ImportedFilmAdmin)
 
