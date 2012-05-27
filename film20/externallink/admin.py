from django.contrib import admin
from film20.externallink.models import ExternalLink

class ExternalLinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'title', 'film', 'person', 'user', 'LANG','status')
    list_filter = ['url_kind']
    raw_id_fields = ['film','person', 'user',]
    search_fields = ('film__title','title')
    
admin.site.register(ExternalLink, ExternalLinkAdmin)