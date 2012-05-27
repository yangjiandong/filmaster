# Create your views here.
try:
    from PIL import Image
except:
    import Image

from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from film20.config.urls import templates
from film20.notification.models import *

from film20.config.urls import templates, full_url
from film20.import_ratings.forms import *
from film20.import_ratings.import_ratings_helper import *
from .forms import LocationForm, ChangePasswordForm, SetPasswordForm, ProfileForm, ConsumerForm, AvatarForm, AvatarCropForm, CustomFilterForm
from django.contrib import messages
from film20.showtimes.models import Channel
from film20.userprofile.models import Avatar
from film20.utils import cache
from film20.core.models import LocalizedProfile
from film20.import_ratings.models import save_ratings_in_db

@login_required
def show_settings(request):
    profile = request.user.get_profile()
    localized_profile = profile.get_localized_profile()
    return render(request, templates['USER_SETTINGS'], {
        'profile': profile,
        'localized': localized_profile
    })

@login_required
def edit_notification_settings(request):
    """
        View used to edit notification settings
    """

    notice_types = NoticeType.objects.all()
    settings_table = []
    enabled_media = [m for m in NOTICE_MEDIA if m.is_enabled(request.user)]
    for notice_type in NoticeType.objects.exclude(hidden=True).order_by('label'):
        if notice_type.user_group == NoticeType.MODERATORS:
            if not NoticeType.is_moderator( request.user ):
                continue

        settings_row = []
        for medium in enabled_media:
            form_label = "%s_%s" % (notice_type.label, medium.id)
            setting = medium.get_notification_setting(request.user, notice_type)
            if request.method == "POST":
                if request.POST.get(form_label) == "on":
                    setting.send = True
                else:
                    setting.send = False
                setting.save()
            if medium.supports(notice_type):
                settings_row.append({"label":form_label, "value":setting.send})
            else:
                settings_row.append(None)
        if settings_row:
            settings_table.append({"notice_type": notice_type, "cells": settings_row})

    notice_settings = {
        "column_headers": [m.display for m in enabled_media],
        "rows": settings_table,
    }

    return render(request, templates['EDIT_NOTIFICATION_SETTINGS'], {
        "media": NOTICE_MEDIA,
        "enabled_media": enabled_media,
        "notice_types": notice_types,
        "notice_settings": notice_settings,
    })


@login_required
def import_ratings(request):
    """
        View used to import rating from other movie sites
    """

    previous_imports = None
    if request.method == "POST":
        if "criticker" in request.POST:
            criticker_form = ImportCritickerFileForm(request.POST, request.FILES)
            if criticker_form.is_valid():
                overwrite = criticker_form.cleaned_data['overwrite']
                reviews = criticker_form.cleaned_data['import_reviews']
                scoring = criticker_form.cleaned_data['score_convertion']
                ratings_file = criticker_form.cleaned_data['file']

                try:
                    ratings_list = parse_criticker_votes(xml_file=ratings_file,\
                                                         score_convertion=scoring,\
                                                         import_reviews=reviews)
                    save_ratings_in_db(request.user, ratings_list, 
                                          ImportRatings.CRITICKER,
                                          overwrite=overwrite)
                    successful = True
                except Exception as e:
                    successful = False

        elif "imdb" in request.POST:
            imdb_form = ImportImdbRatingsForm(request.POST, request.FILES)
            if imdb_form.is_valid():
                ratings_file = imdb_form.cleaned_data['file']
                overwrite = imdb_form.cleaned_data['overwrite']

                try:
                    ratings_list = parse_imdb_votes(ratings_file)
                    save_ratings_in_db(request.user, ratings_list, 
                                       ImportRatings.IMDB, 
                                       overwrite=overwrite)
                    successful = True
                except Exception as e:
                    successful = False
                    
        elif "filmweb" in request.POST:
            filmweb_form = ImportFilmwebRatingsForm(request.POST)
            if filmweb_form.is_valid():
                filmweb_username = filmweb_form.cleaned_data.get('username')
                filmweb_password = filmweb_form.cleaned_data.get('password')
                overwrite = filmweb_form.cleaned_data['overwrite']

                try:
                    FilmwebRatingsFetcher(request.user, filmweb_username, 
                                      filmweb_password, ImportRatings.FILMWEB, 
                                      overwrite=overwrite)
                    successful = True
                except Exception as e:
                    successful = False

        if successful:
            messages.add_message(request, messages.INFO, _("Ratings will be imported in less then 15 minutes!"))
        else:
            logger.error( e )
            messages.add_message(request, messages.INFO, _("We encountered an error:") + " " +  str(e) + ". " + _("Please try again later. If problem seems permanent, please contact with us at") + " " + settings.CONTACT_EMAIL)
            
        return HttpResponseRedirect(reverse(import_ratings))

    previous_imports = ImportRatingsLog.objects.filter(user=request.user).order_by("-created_at")
    criticker_form = ImportCritickerFileForm()
    imdb_form = ImportImdbRatingsForm()
    filmweb_form = ImportFilmwebRatingsForm()

    data = {
        'criticker_form':criticker_form,
        'imdb_form':imdb_form,
        'filmweb_form':filmweb_form,
        'previous_imports':previous_imports,
    }
    return render(request, templates['IMPORT_RATINGS_SETTINGS'], data)


@login_required
def import_summary(request, import_id):
    """
        View used to display import ratings summary
    """
    from film20.config.urls import urls
    import urllib
    summary = get_object_or_404(ImportRatingsLog, user=request.user, id=import_id)
    not_rated = []
    for f in summary.movies_not_rated.split(';'):
        title = f.strip()
        link = '/'+urls['ADD_FILMS']+'/?'+urllib.urlencode({'title':title.encode('utf-8')})
        not_rated.append({'title':title, 'addlink':link})
    data = {
        'summary':summary,
        'not_rated_list': not_rated
    }
    return render(request, templates['IMPORT_RATINGS_SUMMARY_SETTINGS'], data)

@login_required
def edit_location(request):
    """
    Location selection of the user profile
    """
    profile = request.user.get_profile()

    if request.method == "POST":
        form = LocationForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            if profile.any_field_changed('latitude', 'longitude'):
                messages.add_message(request, messages.INFO, _("Your new location has been set"))
            # invalidate personalized recommendations in area cache
            cache.delete(cache.Key("top_personalized_recommendations",
                request.user))
            cache.delete(cache.Key("tv_user_recommended", request.user))
            cache.delete(cache.Key("cinema_user_recommended", request.user))
            next = request.GET.get('next')
            if next:
                return HttpResponseRedirect(next)
    else:
        form = LocationForm(instance=profile)

    template = "usersettings/edit_location.html"
    data = {
        'section': 'location',
        'form': form, 
    }
    return render(request, template, data)

@login_required
def password_change(request):
    if request.user.has_usable_password():
        form_class = ChangePasswordForm 
        message = _(u"Password successfully changed.")
    else:
        form_class = SetPasswordForm
        message = _(u"Password successfully set.")
        
    if request.method == "POST":
        password_change_form = form_class(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
            messages.add_message(request, messages.INFO, message)
            return HttpResponseRedirect(reverse("user_settings"))
    else:
        password_change_form = form_class(request.user)
    return render(request, "usersettings/password_change.html", {
        "form": password_change_form,
    })

@login_required
def edit_profile(request):
    profile = request.user.get_profile()
    localized_profile = profile.get_localized_profile()

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile.user.first_name = form.cleaned_data['first_name']
            profile.user.last_name = form.cleaned_data['last_name']
            profile.user.email = form.cleaned_data['email']
            profile.display_name = form.cleaned_data['display_name']
            profile.user.save()
            
            localized_profile.description = form.cleaned_data['description']
            localized_profile.blog_title = form.cleaned_data['blog_title']
            localized_profile.save()
            
            form.save()
            messages.add_message(request, messages.INFO, _("Your profile has been chaged"))
    else:
        form = ProfileForm(instance=profile, 
            initial={
                     'first_name':profile.user.first_name,
                     'last_name':profile.user.last_name,
                     'email':profile.user.email,
                     'display_name':profile.display_name,
                     'description':localized_profile.description,
                     'blog_title':localized_profile.blog_title,
                    }
        )

    return render(request, "usersettings/edit_profile.html", {
        'form': form
    })

from piston.models import Consumer, Token

@login_required
def applications(request):
    consumers = Consumer.objects.filter(user=request.user)
    tokens = Token.objects.all().filter(user=request.user, token_type=Token.ACCESS)
    return render(request, "usersettings/applications.html", {
        'consumers': consumers,
        'tokens': tokens,
    })

@login_required
def add_application(request):
    form = ConsumerForm(request.POST or None)
    if request.POST and form.is_valid():
        consumer = form.save(commit = False)
        consumer.user = request.user
        consumer.generate_random_codes()
        return HttpResponseRedirect(reverse(view_application, args=[consumer.pk]))
    return render(request, "usersettings/add_application.html", {
        'form':form,
    })

@login_required
def view_application(request, id):
    return render(request, "usersettings/view_application.html", {
        'consumer':get_object_or_404(Consumer, pk=id, user=request.user)
    })

@login_required
def remove_access_token(request, id):
    get_object_or_404(Token, pk=id, user=request.user).delete()
    return HttpResponseRedirect(reverse(applications))

@login_required
def remove_application(request, id):
    get_object_or_404(Consumer, pk=id, user=request.user).delete()
    return HttpResponseRedirect(reverse(applications))

@login_required
def tvchannels(request):
    """
    user TVChannel selection view
    """
    from forms import TVChannelsForm
    from film20.showtimes.models import TYPE_TV_CHANNEL, UserChannel

    profile = request.user.get_profile()
    user_channels = list(u.pk for u in request.user.selected_channels.filter(type=TYPE_TV_CHANNEL))

    queryset = Channel.objects.tv().filter(is_active=True)
    if profile.country:
        queryset = queryset.filter(country__code=profile.country)

    is_post = request.method == 'POST'
    form = TVChannelsForm(request.POST if is_post else None, initial={'channels':user_channels})
    form.fields['channels'].choices = [(c.id, c.name) for c in queryset]
    if is_post:
        if form.is_valid():
            channels = form.cleaned_data['channels']
            UserChannel.objects.filter(
                    user=request.user, 
                    channel__type=TYPE_TV_CHANNEL,
                    channel__country__code=profile.country,
            ).delete()
            logger.info(channels)
            for c in channels:
                UserChannel(user=request.user, channel_id=c).save()
            # invalidate personalized recommendations in area cache
            cache.delete(cache.Key("top_personalized_recommendations",
                request.user))
            cache.delete(cache.Key("tv_user_recommended", request.user))
            cache.delete(cache.Key("cinema_user_recommended", request.user))
    
    ctx = dict(
        form=form,
        channels=list(queryset),
    )
    return render(request, "usersettings/tvchannels.html", ctx)

@login_required
def edit_avatar(request):
    profile = request.user.get_profile()
    if request.method == "POST":
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data.get( 'photo' ) or form.cleaned_data.get( 'url' )
            avatar = Avatar( user=request.user, image=image, valid=False )
            avatar.image.save( "%s.jpg" % request.user.username, image )
            image = Image.open( avatar.image.path )
            image.thumbnail( ( 480, 480 ), Image.ANTIALIAS )
            image.convert( "RGB" ).save( avatar.image.path, "JPEG" )
            avatar.save()
            
            return HttpResponseRedirect( reverse( 'crop_avatar' ) )
    else:
        form = AvatarForm()


    ctx = dict(
        form=form,
    )

    return render( request, "usersettings/edit_avatar.html", ctx )

@login_required
def crop_avatar( request ):
    avatar = get_object_or_404( Avatar, user=request.user, valid=False )
    if request.method == "POST":
        form = AvatarCropForm( request.POST )
        if form.is_valid():
            top = int( form.cleaned_data.get( 'top' ) )
            left = int( form.cleaned_data.get( 'left' ) )
            right = int( form.cleaned_data.get( 'right' ) )
            bottom = int( form.cleaned_data.get( 'bottom' ) )

            image = Image.open( avatar.image.path )
            box = [ left, top, right, bottom ]
            image = image.crop( box )
            if image.mode not in ( 'L', 'RGB' ):
                image = image.convert( 'RGB' )
            image.save( avatar.image.path )
            
            avatar.valid = True
            avatar.save()
            
            return HttpResponseRedirect( reverse( "edit_avatar" ) )
    else:
        form = AvatarCropForm()

    ctx = dict(
        form=form,
        avatar=avatar,
    )

    return render( request, "usersettings/crop_avatar.html", ctx )

@login_required
def delete_avatar( request ):
    avatar = get_object_or_404( Avatar, user=request.user, valid=True )
    avatar.delete()
    
    return HttpResponseRedirect( reverse( "edit_avatar" ) )


@login_required
def associations(request):
    from film20.facebook_connect.models import FBAssociation
    from film20.facebook_connect.utils import get_facebook_cookie
    from django_openidconsumer import views as openid_consumer_views
    from django_openidauth.models import UserOpenID, associate_openid, unassociate_openid
    from film20.account.models import OAuthService, OAUTH_SERVICES
    from django.contrib.auth import BACKEND_SESSION_KEY, load_backend
    from film20.facebook_connect.facebookAuth import FacebookBackend

    openid_url = request.POST.get('openid_url')
    if openid_url:
        # They entered a new OpenID and need to authenticate it - kick off the
        # process and make sure they are redirected back here afterwards
        def openid_failure(request,message):
          return message
        ret = openid_consumer_views.begin(request, redirect_to=reverse('openid_complete'), on_failure=openid_failure)
        if isinstance(ret, (str, unicode)) or isinstance(ret,unicode):
            messages.add_message(request, messages.ERROR, ret)
        else:
          return ret
    try:
        fb_association = FBAssociation.objects.get(user=request.user)
    except FBAssociation.DoesNotExist, e:
        fb_association = None

    used = [o.openid for o in request.openids]

    remove_openid = request.POST.get('remove_openid')
    if remove_openid and remove_openid not in used:
        unassociate_openid(request.user, remove_openid)
        return HttpResponseRedirect(reverse(associations))

    openids = list(UserOpenID.objects.filter(user=request.user).order_by('created_at'))
    for o in openids:
        o.is_used = o.openid in used

    class Association(object):
        def __init__(self, service):
            self.service = service

        def is_associated(self):
            return bool(self.service.get_user_id(request.user))

        def is_logged_in(self):
            return getattr(backend, 'service_class', None) == self.service.__class__

    backend = load_backend(request.session[BACKEND_SESSION_KEY])

    oauth_associations = (Association(service) for service in OAUTH_SERVICES)

    error = request.GET.get('error')
    if error:
        messages.add_message(request, messages.ERROR, error)

    ctx = {
        'fb_association': fb_association,
        'oauth_associations': oauth_associations,
        'openids': openids,
        'fc': isinstance(backend, FacebookBackend),
    }

    return render(request, "usersettings/associations.html", ctx)

@login_required
def dashboard_settings( request ):
    profile = request.user.get_profile()
    initial = { 'custom_filter': profile.custom_dashboard_filter, 
                'activities_on_dashboard': profile.activities_on_dashboard }

    form = CustomFilterForm( initial=initial )
    if request.method == 'POST':
        form = CustomFilterForm( request.POST )
        if form.is_valid():
            profile.custom_dashboard_filter = form.cleaned_data['custom_filter']
            profile.activities_on_dashboard = form.cleaned_data['activities_on_dashboard']
            profile.save()
        
            messages.add_message( request, messages.INFO, _( "Settings saved!" ) )

    return render( request, "usersettings/dashboard_settings.html", { 'form': form } )
 
