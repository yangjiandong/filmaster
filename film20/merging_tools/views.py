import json

from django.db import transaction
from django.core.files.images import ImageFile, get_image_dimensions
from django.template import RequestContext
from django.http import Http404, HttpResponse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from film20.blog.models import Post
from film20.tagging.models import Tag
from film20.showtimes.models import Screening
from film20.filmbasket.models import BasketItem
from film20.moderation.registry import registry
from film20.useractivity.models import UserActivity
from film20.merging_tools.util import Preview, get_related_objects
from film20.merging_tools.models import DuplicatePerson, DuplicateFilm
from film20.core.models import Film, Rating, Character, ShortReview, ObjectLocalized
from film20.showtimes.models import FilmOnChannel, ScreeningCheckIn
from film20.merging_tools.forms import ReportPersonDuplicateForm, ReportFilmDuplicateForm
from film20.core import rating_helper

from django.core.exceptions import PermissionDenied

def superuser_required( function ):
    def _inner( request, *args, **kwargs ):
        if not request.user.is_superuser:
            raise PermissionDenied
        return function( request, *args, **kwargs )
    return _inner


def item_formater( obj, request ):
    if isinstance( obj, Character ):
        return mark_safe( '%s, <a href="%s">%s</a>' % ( obj, obj.film.get_absolute_url(), obj.film ) )

    if isinstance( obj, Film ):
        return mark_safe( '<a href="%s">%s</a>' % ( obj.get_absolute_url(), obj ) )

    if isinstance( obj, Post ):
        return mark_safe( '<a href="%s">%s</a>' % ( obj.get_absolute_url(), obj.get_title() ) )

    if isinstance( obj, UserActivity ):

        from django.template import loader
        res = loader.render_to_string( "wall/useractivity/show_activities.html", 
                                    { 'activities': [ obj ] }, context_instance=RequestContext( request ) )

        return mark_safe( res )

    if isinstance( obj, ImageFile ):
        return mark_safe( '<img src="%s" alt="%s">' % ( obj.url, obj ) )

    if isinstance( obj, BasketItem ):
        return mark_safe( '%s, %s %s' % ( obj.user, obj.show_wishlist(), obj.show_owned() ) )

    return mark_safe( str( obj ) )


@login_required
def request_duplicate( request, type ):

    if type not in ['film', 'person']:
        raise Http404

    forms = {
        'film': ReportFilmDuplicateForm,
        'person': ReportPersonDuplicateForm
    }

    result = {
        'success': False,
        'message': '',
    }

    if request.method == "POST":
        form = forms[type]( request.POST )

        if form.is_valid():
            cleaned_data = form.cleaned_data
            objectA = cleaned_data.get( 'objectA' )
            objectB = cleaned_data.get( 'objectB' )

            if type == 'person':
                duplicate_object, created = DuplicatePerson.objects.get_or_create( user=request.user,
                                                                                        personA=objectA, personB=objectB )

            else:
                duplicate_object, created = DuplicateFilm.objects.get_or_create( user=request.user,
                                                                                        filmA=objectA, filmB=objectB )

            result['success'] = True
            result['message'] = _( "Thank you for you suggestion!" )

        else:
            result['errors'] = dict([(k, [unicode(e) for e in v]) for k,v in form.errors.items()])

        return HttpResponse( json.dumps( result ), mimetype="text/javascript" )

    else:
        return render( request, "moderation/merging_tools/request.html", {
            "form": forms[type](),
        })


@superuser_required
def people_merging( request ):
    items = DuplicatePerson.objects.filter( resolved=False )
    moderated_items = registry.get_by_user( request.user )

    return render( request, "moderation/merging_tools/people/index.html", { 
        "items": items,
        "moderated_items": moderated_items['items'],
        "moderator_tools": moderated_items['tools'],
    })

@superuser_required
def people_merging_resolve( request, id ):
    dp = get_object_or_404( DuplicatePerson, pk=id )
    step = int( request.POST.get( 'step', 1 ) )

    moderated_items = registry.get_by_user( request.user )
    ctx = {
        "step": step,
        "duplicate_person": dp,
        "moderated_items": moderated_items['items'],
        "moderator_tools": moderated_items['tools'],
    }

    if step > 1:
        if 'A' in request.POST:
            option    = 'A'
            selected  = dp.personA
            to_delete = dp.personB

        else:
            option    = 'B'
            selected  = dp.personB
            to_delete = dp.personA

        ctx['option']    = option
        ctx['selected']  = selected
        ctx['to_delete'] = to_delete

        if step in [2, 3]:
            save = ( step == 3 )

            preview = Preview( request, item_formater ) if not save else None

            do_people_merging_resolve( selected, to_delete, preview )

            if not save:
                ctx['preview'] = preview
                ctx['objects_to_delete'] = get_related_objects( [to_delete] )

    return render( request, "moderation/merging_tools/people/resolve-step-%d.html" % step, ctx )


def do_people_merging_resolve( selected, to_delete, preview = None ):

    save = preview is None

    with transaction.commit_on_success():
        has_photo = selected.image or selected.hires_image
        
        # 1. merge all activities reloated to that person
        for ua in UserActivity.all_objects.filter( person=to_delete ):

            # remove deleted object photo activity if selected person already has
            if has_photo and ua.activity_type == UserActivity.TYPE_POSTER:
                if save:
                    ua.delete()

                else:
                    preview.add_item( _( 'UserActivity to remove' ), ua,
                                        _( "will be removed becouse person already has image" ) )
                continue
            
            # update poster related fields
            if ua.activity_type == UserActivity.TYPE_POSTER:
                if save:
                    ua.object_title = str( selected );
                    ua.object_slug = selected.permalink
            
            # person wallpost 
            elif ua.activity_type == UserActivity.TYPE_SHORT_REVIEW:
                if save:
                    ua.object = selected
                    ua.watching_object = selected
                    ua.title = str( selected )
           
            if save:
                ua.person = selected
                ua.save()
            else:
                preview.add_item( _( 'UserActivity to update' ), ua, _( "will be updated to point selected person" ) )

        # 2. merge person photo
        if not has_photo and ( to_delete.hires_image or to_delete.image ):
            if save:
                selected.image = to_delete.image
                selected.hires_image = to_delete.hires_image
            else:
                preview.add_item( _( 'Photo to replace' ), to_delete.hires_image or to_delete.image
                                    , _( "the image will be taken from object to delete" ) )

        # 3. update links to that person in all the films he's eiter acting or directing
        for character in Character.objects.filter( person=to_delete ):
            if save:
                character.person = selected
                character.save()
            else:
                preview.add_item( 'Character to replace', character, _( "this characters will be updated" ) )

        # ordering ???
        for film in Film.objects.filter( directors__in=[to_delete] ):
            if save:
                film.directors.remove( to_delete )
                film.directors.add( selected )
                film.save()

            else:
                preview.add_item( 'Director to replace', film, _( "the director of this movies will be updated" ) )

        # 4. update all the ratings of this person
        for rating in Rating.objects.filter( director=to_delete ):
            try:
                selected_rating = Rating.objects.get( director=selected, type=rating.type, user=rating.user )
                if save:
                    rating_helper.rate(rating.user, None, director_id=to_delete.id, type=rating.type)
                else:
                    preview.add_item( 'Director rating to delete', rating, _( "the director rating to delete - user rated both" ) )

            except Rating.DoesNotExist:
                if save:
                    rating_helper.rate(rating.user, rating.rating, director_id=selected.id, type=rating.type)
                    rating_helper.rate(rating.user, None, director_id=to_delete.id, type=rating.type)

                else:
                    preview.add_item( 'Director rating to update', rating, _( "the director rating to update" ) )

        for rating in Rating.objects.filter( actor=to_delete ):
            try:
                selected_rating = Rating.objects.get( actor=selected, type=rating.type, user=rating.user )
                if save:
                    rating_helper.rate(rating.user, None, actor_id=to_delete.id, type=rating.type)
                else:
                    preview.add_item( 'Actor rating to delete', rating, _( "the actor rating to delete - user rated both" ) )

            except Rating.DoesNotExist:
                if save:
                    rating_helper.rate(rating.user, rating.rating, actor_id=selected.id, type=rating.type)
                    rating_helper.rate(rating.user, None, actor_id=to_delete.id, type=rating.type)

                else:
                    preview.add_item( 'Actor rating to update', rating, _( "the actor rating to update" ) )

        # 5. short reviews
        for review in ShortReview.all_objects.filter( object__pk=to_delete.pk ):
            if save:
                review.object=selected
                review.save()

            else:
                preview.add_item( 'Short Review to update', review, _( "the related object of this short review will be updated" ) )


        # 6. articles
        for post in Post.objects.filter( related_person__pk=to_delete.pk ):
            if save:
                post.related_person.remove( to_delete )
                post.related_person.add( selected )
                post.save()

            else:
                preview.add_item( 'Article to update', post, _( "the related person of this article will be updated" ) )

        # 7. delete object
        if save:
            to_delete.delete()
            selected.save()


@superuser_required
def film_merging( request ):
    items = DuplicateFilm.objects.filter( resolved=False )
    moderated_items = registry.get_by_user( request.user )

    return render( request, "moderation/merging_tools/movies/index.html", { 
        "items": items,
        "moderated_items": moderated_items['items'],
        "moderator_tools": moderated_items['tools'],
    })


@superuser_required
def film_merging_resolve( request, id ):
    dp = get_object_or_404( DuplicateFilm, pk=id )
    step = int( request.POST.get( 'step', 1 ) )

    moderated_items = registry.get_by_user( request.user )
    ctx = {
        "step": step,
        "duplicate_film": dp,
        "moderated_items": moderated_items['items'],
        "moderator_tools": moderated_items['tools'],
    }

    if step == 1:
        ctx['stats'] = {
            'number_of_ratings': {
                'A': Rating.objects.filter( film=dp.filmA ).count(),
                'B': Rating.objects.filter( film=dp.filmB ).count(),
            },
            'number_of_activities': {
                'A': UserActivity.all_objects.filter( film=dp.filmA ).count(),
                'B': UserActivity.all_objects.filter( film=dp.filmB ).count(),
            }
        }

    elif step > 1:
        if 'A' in request.POST:
            option    = 'A'
            selected  = dp.filmA
            to_delete = dp.filmB

        else:
            option    = 'B'
            selected  = dp.filmB
            to_delete = dp.filmA

        ctx['option']    = option
        ctx['selected']  = selected
        ctx['to_delete'] = to_delete

        if step in [2, 3]:
            save = ( step == 3 )

            if not save:
                preview = Preview( request, item_formater )

            with transaction.commit_on_success():
                has_photo = selected.image or selected.hires_image

                # 1. update tags
                tags = { 
                    'en': [],
                    'pl': [] 
                }

                for lang in ( 'en', 'pl' ):
                    for flm in ( to_delete, selected ):
                        try:
                            film_localized = ObjectLocalized.objects.get( parent=flm.id, LANG=lang )
                            for tag in Tag.objects.get_for_object( film_localized ):
                                if not tag.name in tags[lang]:
                                    tags[lang].append( tag.name )

                        except ObjectLocalized.DoesNotExist: 
                            pass

                for lang in ( 'en', 'pl' ):
                    if len( tags[lang] ):
                        tag_list = ", ". join( tags[lang] )
                        if save:
                            selected.save_tags( tag_list, lang )
                        else:
                            preview.add_item( _( 'Merged tags' ), "<strong>%s</strong>: %s" % ( lang, tag_list ), "" )
            

                # 2. update wishlist and owned 
                for bi in BasketItem.objects.filter( film=to_delete ):
                    try:
                        BasketItem.objects.get( film=selected, user=bi.user )

                    except BasketItem.DoesNotExist: 
                        if save:
                            bi.film = selected
                            bi.save()

                        else:
                            preview.add_item( _( 'Basket item to update' ), bi, "" )

               
                # 3. merge all activities reloated to that film
                for ua in UserActivity.all_objects.filter( film=to_delete ):

                    # remove deleted object photo activity if selected film already has
                    if has_photo and ua.activity_type == UserActivity.TYPE_POSTER:
                        if save:
                            ua.delete()

                        else:
                            preview.add_item( _( 'UserActivity to remove' ), ua,
                                                _( "will be removed because the film already has image" ) )
                        continue
                     
                    if save:
                        # film wallpost 
                        if ua.activity_type == UserActivity.TYPE_SHORT_REVIEW:
                            ua.object = selected
                            ua.watching_object = selected
                            ua.title = str( selected )
 
                        ua.film = selected
                        ua.film_title = selected.get_title();
                        ua.film_slug = selected.permalink
                        ua.save()

                    else:
                        preview.add_item( _( 'UserActivity to update' ), ua, _( "will be updated to point to a selected film" ) )

                # 3. merge film photo
                if not has_photo and ( to_delete.hires_image or to_delete.image ):
                    if save:
                        selected.image = to_delete.image
                        selected.hires_image = to_delete.hires_image
                    else:
                        preview.add_item( _( 'Photo to replace' ), to_delete.hires_image or to_delete.image
                                            , _( "the image will be taken from object to delete" ) )

                # 4. update all the ratings of this film
                for rating in Rating.objects.filter( film=to_delete, rating__isnull=False ):
                    try:
                        selected_rating = Rating.objects.get( film=selected, type=rating.type, user=rating.user )
                        if save:
                            rating_helper.rate(rating.user, None, film_id=to_delete.id, type=rating.type)
                        else:
                            preview.add_item( 'Film rating to delete', rating, _( "the film rating to delete - user rated both films" ) )

                    except Rating.DoesNotExist:
                        if save:
                            rating_helper.rate(rating.user, rating.rating, film_id=selected.id, type=rating.type)
                            rating_helper.rate(rating.user, None, film_id=to_delete.id, type=rating.type)
                        else:
                            preview.add_item( 'Film rating to update', rating, _( "the film rating to update" ) )

                # 5. short reviews
                for review in ShortReview.all_objects.filter( object__pk=to_delete.pk ):
                    if save:
                        review.object=selected
                        review.save()

                    else:
                        preview.add_item( 'Short Review to update', review, _( "the related object of this short review will be updated" ) )


                # 6. articles
                for post in Post.objects.filter( related_film__pk=to_delete.pk ):
                    if save:
                        post.related_film.remove( to_delete )
                        post.related_film.add( selected )
                        post.save()

                    else:
                        preview.add_item( 'Article to update', post, _( "the related film of this article will be updated" ) )

                # 7. showtimes
                for foch in FilmOnChannel.objects.filter( film=to_delete ):
                    if save:
                        foch.film = selected
                        foch.save()

                    else:
                        preview.add_item( 'Film on channel to update', foch, "" )

                for checkin in ScreeningCheckIn.objects.filter( film=to_delete ):
                    if save:
                        checkin.film = selected
                        checkin.save()

                    else:
                        preview.add_item( 'Checkin to update', checkin, "" )


                # 8. delete object
                if save:
                    to_delete.delete()
                    selected.save()

                else:
                    ctx['preview'] = preview
                    ctx['objects_to_delete'] = get_related_objects( [to_delete] )

    return render( request, "moderation/merging_tools/movies/resolve-step-%d.html" % step, ctx )

