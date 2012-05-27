from django.conf.urls.defaults import *
from film20.config.urls import urls
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from film20.usersettings.views import show_settings

urlpatterns = patterns('film20.usersettings.views',
    url(r'^$', show_settings, name='user_settings'),
    url(r'^%(MANAGE_NOTIFICATIONS)s/$' % urls, 'edit_notification_settings', name='edit_notification_settings'),
    url(r'^%(IMPORT_RATINGS)s/$' % urls, 'import_ratings', name='import_ratings'),
    url(r'^%(IMPORT_RATINGS)s/(?P<import_id>\d{1,10})/$' % urls, 'import_summary', name='import_summary'),
    url(r'^%(EDIT_LOCATION)s/$' % urls, 'edit_location', name='edit_location'),
    url(r'^%(CHANGE_PASSWORD)s/$' % urls, 'password_change', name='change_password'),
    url(r'^%(EDIT_PROFILE)s/$' % urls, 'edit_profile', name='edit_profile'),
    url(r'^%(EDIT_AVATAR)s/$' % urls, 'edit_avatar', name='edit_avatar'),
    url(r'^%(CROP_AVATAR)s/$' % urls, 'crop_avatar', name='crop_avatar'),
    url(r'^%(DELETE_AVATAR)s/$' % urls, 'delete_avatar', name='delete_avatar'),
    # Applications
    url(r'^%(APPLICATIONS)s/$' % urls, 'applications', name='applications'),
    url(r'^%(ADD_APPLICATION)s/$' % urls, 'add_application', name='add_application'),
    url(r'^%(APPLICATION)s/(?P<id>\d+)/$' % urls, 'view_application', name='view_application'),
    url(r'^%(REMOVE_ACCESS_TOKEN)s/(?P<id>\d+)/$' % urls, 'remove_access_token', name='remove_access_token'),
    url(r'^%(REMOVE_APPLICATION)s/(?P<id>\d+)/$' % urls, 'remove_application', name='remove_application'),
    url(r'^%(TV_CHANNELS)s/$' % urls, 'tvchannels', name='user_tvchannels'),        
    url(r'^%(ASSOCIATIONS)s/$' % urls, 'associations', name="associations"),
    url(r'^%(DASHBOARD_SETTINGS)s/$' % urls, 'dashboard_settings', name="dashboard_settings"),
)
