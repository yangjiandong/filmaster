from django.contrib import admin

from film20.oembed.models import ProviderRule, StoredOEmbed

admin.site.register(ProviderRule)
admin.site.register(StoredOEmbed)
