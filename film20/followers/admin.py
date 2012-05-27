from film20.followers.models import Followers
from django.contrib import admin

class FollowersAdmin(admin.ModelAdmin):
    raw_id_fields = ['from_user', 'to_user']

admin.site.register(Followers, FollowersAdmin)
  