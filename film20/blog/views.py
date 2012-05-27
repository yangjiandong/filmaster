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
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import redirect_to
from film20.blog.models import Blog, Post
from film20.config.urls import templates, full_url
from django.views.generic.list_detail import object_list
from film20.blog.forms import BlogSettingsForm, BlogPostForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.template import RequestContext
from film20.core.models import Object, Film, Character, LocalizedProfile
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from film20.threadedcomments.models import ThreadedComment
from film20.recommendations.recom_helper import RecomHelper
from film20.core.object_helper import UserComparator
from film20.core.forms import *
from film20.utils.slughifi import slughifi
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

import logging
logger = logging.getLogger(__name__)
import re
from film20.useractivity.forms import SuperForm
from film20.utils.utils import *
from film20.useractivity.models import UserActivity

MAX_RELATED_REVIEWS = 5

def show_blog_post(request, permalink, user_name):
    profile = None
    user_comparator = None
    author_ratings = None

    logger.debug(user_name)
    logger.debug(request.build_absolute_uri())
    try:
        user = User.objects.get(username__iexact=user_name)
        username = user.username
        other_user = user
        profile = user.get_profile()               
    except:
        raise Http404

    if request.user == other_user:
        is_me = True
    else:
        is_me = False

    if _("preview") in request.GET and request.user==user:
        posts = Post.objects.filter(user__username__iexact=user_name, permalink = permalink).exclude(status=Post.DELETED_STATUS)
        logger.debug(posts)
        if len(posts)==0:
            raise Http404
        else:
            post = posts[0]    
    else:
        try:
            post = Post.objects.select_related().get(user__username__iexact=user_name,
                                                     permalink = permalink, status=Post.PUBLIC_STATUS)
        except:
            raise Http404
            
    #profile = post.author.user.get_profile()
    related_films = None
    related_people = None
    other_user_posts = Post.objects.select_related().filter(user=user, status=Post.PUBLIC_STATUS)\
                                                    .exclude(id=post.id)[:MAX_RELATED_REVIEWS]
    other_posts_for_film = None
    related_films = post.related_film.select_related()
    
    the_film = None # to be used for ratings
    for related_film in related_films:
        the_film = related_film       
        related_posts = Post.objects.select_related().filter(related_film=related_film,\
                                                             status=Post.PUBLIC_STATUS)\
                                                      .exclude(id=post.id)[:MAX_RELATED_REVIEWS]
        if related_posts != None:
            if len(related_posts)>0:
                other_posts = [related_film, related_posts]
                if other_posts_for_film == None:
                    other_posts_for_film = []
                other_posts_for_film.append(other_posts)
        
    related_people = post.related_person.select_related()
    
    if (len(related_films) == 1) & (the_film != None):
        from film20.core import rating_helper
        author_ratings = rating_helper.get_ratings_for_user_and_film(user, the_film)


    # get the comparator
    if request.user.is_authenticated():      
        recom_helper = RecomHelper()      
        rating_comparator = recom_helper.get_rating_comparator_for_user(request.user, user)
        if rating_comparator!= None:
            user_comparator = UserComparator(rating_comparator.score)

    from film20.useractivity.watching_helper import WatchingHelper
    subscribe_form = None
    subscribe_action = None
    # subscription form
    if request.user.is_authenticated():     
        watching_helper = WatchingHelper()
        subscribe_action = watching_helper.get_subscribe_action(request.user, post)
        subscribe_form = watching_helper.get_subscribe_form(post, subscribe_action)
    
    data = {
        'post' : post, 
        'related_films' : related_films, 
        'related_people' : related_people,
        'profile':profile,
        'other_user_posts':other_user_posts,
        'other_posts_for_film':other_posts_for_film, 
        'author_ratings' : author_ratings,
        'user_comparator': user_comparator,

        'subscribe_form': subscribe_form,
        'subscribe_action': subscribe_action,
        
        # friendship
        "is_me": is_me,
        "is_friend": None,
        "invite_form": None,
        "other_friends": None,
        "other_user": other_user,
        "previous_invitations_to": None,
        "previous_invitations_from": None,
    }

    return render_to_response(templates['SHOW_NOTE'],
        data, 
        context_instance=RequestContext(request))
    
@login_required
def add_blog_post(request, film_id=None):
    #blog_object = Blog.objects.get_or_create(user=request.user, LANG=LANGUAGE_CODE)
    if request.method == "POST":
        logger.debug('Request is post')
        form = BlogPostForm(request.user, request.POST)
        if form.is_valid():
            logger.debug('Form is valid')
            blog = form.save(commit=False)
            #blog_instance = blog_object[0]
            #blog.author = blog_instance
            blog.user = request.user
            blog.creator_ip = request.META['REMOTE_ADDR']
            blog.type = Object.TYPE_POST
            blog.version = 0
            if "save" in request.POST:
                blog.status = Post.DRAFT_STATUS
                request.user.message_set.create(message=_("Successfully saved post '%s'. You have saved the review as draft. If you want to make it visible to others, you need to publish it.") % blog.title)
            if "publish" in request.POST:
                blog.status = Post.PUBLIC_STATUS
                request.user.message_set.create(message=_("Successfully published post '%s'.") % blog.title)
            blog.save()
            form.save_m2m()
            blog.save()
            return HttpResponseRedirect(reverse(edit_blog))
    else:
        related_film = None
        related_people = ""
        if film_id:
            try:
                related_film = Film.objects.get(pk=film_id)
            except Film.DoesNotExist:
                related_film = None
            directors = related_film.directors.select_related()
            for director in directors:
                related_people = related_people + unicode(director) + ", "
            actors = Character.objects.filter(film=related_film).order_by("importance")[:5]
            for actor in actors:
                 related_people = related_people + unicode(actor.person) + ", "
        form = BlogPostForm(initial={'related_film': comma_escape(unicode(related_film)), 'related_person':related_people})
        return render_to_response(templates['EDIT_NOTE'], {'form' : form}, context_instance=RequestContext(request))
    return render_to_response(templates['EDIT_NOTE'], {'form' : form}, context_instance=RequestContext(request))

@login_required
def edit_blog(request):
    profile = LocalizedProfile.objects.get_for(request.user)
    posts = Post.objects.filter(Q(user=request.user), Q(status = Post.PUBLIC_STATUS)|Q(status = Post.DRAFT_STATUS)).order_by('-publish')
    #obsluga formularza zmiany tytulu bloga
    if request.method == "POST":
        form = BlogSettingsForm(request.POST)
        if form.is_valid():
            profile.blog_title = form.cleaned_data['blog_title']
            profile.save()
            
            return HttpResponseRedirect(reverse(edit_blog))
    else:
        form = BlogSettingsForm(initial={'blog_title':profile.blog_title})
        return render_to_response(templates['EDIT_BLOG'], {'posts' : posts, 'form' : form}, context_instance=RequestContext(request))
    return render_to_response(templates['EDIT_BLOG'], {'posts' : posts, 'form' : form} , context_instance=RequestContext(request))

@login_required
def edit_blog_post(request, permalink=None, post_id=None):
    user = request.user
    try:
        if permalink is not None:
            # user is trying to edit post from profile
            post = Post.objects.get(Q(permalink=permalink),Q(user=user), Q(status = Post.PUBLIC_STATUS)|Q(status = Post.DRAFT_STATUS))
        else:
            # user is trying to edit post from planet
            post = Post.objects.get(Q(id=post_id),Q(user=user), Q(status = Post.PUBLIC_STATUS)|Q(status = Post.DRAFT_STATUS))
    except Post.DoesNotExist:
        raise Http404

    next = request.META.get('HTTP_REFERER', None)
    if request.method == 'POST':
        form = BlogPostForm(request.user, request.POST, instance=post)
        if form.is_valid():
            blog = form.save(commit=False)
            if "save" in request.POST:
                request.user.message_set.create(message=_("Successfully saved post '%s'.") % blog.title)
            if "unpublish" in request.POST:
                blog.status = Post.DRAFT_STATUS
                request.user.message_set.create(message=_("Successfully unpublished post '%s'.") % blog.title)
            if "publish" in request.POST:
                blog.status = Post.PUBLIC_STATUS
                request.user.message_set.create(message=_("Successfully published post '%s'.") % blog.title)

            blog.save()
            form.save_m2m()
            #saving activity here because many-to-many relation
            blog.save_activity()
            blog.update_activity()
            if next is not None:
                is_preview = re.search("\?"+_("preview"), next)
            if next is None:
                next = full_url('EDIT_NOTE')
            elif is_preview:
                next = full_url('EDIT_NOTE')
            #request.user.message_set.create(message=_("Successfully saved post '%s'") % blog.title)     
            return HttpResponseRedirect(next) 
    else:
        related_movies = post.related_film.select_related()
        related_people = post.related_person.select_related()        
        related_names = get_related_people_as_comma_separated_string(related_people)
        related_film = ', '.join(comma_escape(unicode(m)) for m in related_movies)
        form = BlogPostForm(instance=post, initial={'related_film': related_film, 'related_person':related_names})
        return render_to_response(templates['EDIT_NOTE'],{'form':form,'next':next,'post':post}, context_instance=RequestContext(request))
    return render_to_response(templates['EDIT_NOTE'],{'form':form,'next':next,'post':post}, context_instance=RequestContext(request))

@login_required
def delete_post(request, permalink):
    try: 
        post = Post.objects.get(parent__permalink = permalink, user=request.user)
        post.status = Post.DELETED_STATUS
        post.save()
        request.user.message_set.create(message=_("Successfully deleted post '%s'") % post.title)
        return HttpResponseRedirect(reverse(edit_blog))
    except Post.DoesNotExist:
        return HttpResponseRedirect(reverse(edit_blog))

def search_blog(request, user_name):
    results = User.objects.filter(author__icontains=user_name).distinct()
    return render_to_response('search_blog.html', {'results':results})

@login_required
def add_super_form_note(request, ajax=None):
    if request.method == 'POST':
        blog_object = Blog.objects.select_related().get_or_create(user=request.user)
        form = SuperForm(request.POST)
        if form.is_valid():
            post = Post()
            post.author = blog_object[0]
            post.body = form.cleaned_data["body"]
            txt = " ".join(post.body.split(' '))[:50]
            if form.cleaned_data["related_film"]:
                post.title = _('Review') + ": " + form.cleaned_data["related_film"][0].title
                post.title = post.title[:200]
                permalink = slughifi(post.title + " " + txt)
            else:
                post.title = _('Review') +": " + txt
                post.title = post.title[:200]
                permalink = slughifi(post.title[:128])
            post.type = Post.TYPE_POST
            post.status = Post.PUBLIC_STATUS
            post.save(permalink=permalink)
            for film in form.cleaned_data["related_film"]:post.related_film.add(film)
            if ajax=="json":
                context = {
                    'success': True,
                    'data': post.id,
                    }
                return json_return(context)
            else:
                return HttpResponseRedirect(full_url("PLANET"))
        else:
            if ajax == "json":
                context = {
                    'success': False,
                    'errors': str(form.errors),
                }
                return JSONResponse(context, is_iterable=False)

    else:
        return HttpResponseRedirect(full_url("PLANET"))

@login_required
def note_partial(request, post_id):
    activity = get_object_or_404(UserActivity, post__id=post_id)

    return render_to_response(
            templates['NOTE_PARTIAL'],
            {'activity':activity,},
            context_instance=RequestContext(request))
