# Python
import logging

# Django
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template.context import RequestContext
from django.template import Context, loader
from django.utils.translation import ugettext as _
from django.db.models import Q

# Project
from film20 import settings
from film20.config import urls
from film20.blog.models import Post
from film20.blog.forms import BlogPostForm
from film20.config.urls import templates
from film20.core.models import ShortReview, Rating, Film
from film20.useractivity.models import UserActivity
from film20.dashboard.forms import WallForm
from film20.utils.slughifi import slughifi
from film20.utils.posters import get_image_path
from film20.recommendations.recom_helper import RecomHelper

from film20.core.templatetags.map_url import permalink_film
from film20.core.templatetags.posters import Thumbnail # FLM-1267
    
logger = logging.getLogger(__name__)

from film20.useractivity.views import WallView

class ShowDashboardView(WallView):
    template_name = templates['DASHBOARD']

    def get_context_data(self, **kw):
        context = super(ShowDashboardView, self).get_context_data(**kw)
        context['profile'] = self.request.user.get_profile()
        context['has_following'] = \
                len(self.request.user.followers.following()) > 0
        context['follow_tab'] = self.request.GET.get('u') == 'followed'
        return context

show_dashboard = login_required(ShowDashboardView.as_view())

@login_required
def _show_dashboard(request):
    """
        Show dashboard for logged in user
    """
    from film20.useractivity.useractivity_helper import ajax_activity_pager, \
        ajax_select_template
        
    filter = None
    user = request.user
    profile = user.get_profile()

    # handle wall post form
    if request.method == "POST":
        form = WallForm(request.POST)
        if form.is_valid():
            sr = ShortReview(kind=ShortReview.WALLPOST,
                             user=user,
                             review_text=form.cleaned_data['text'],
                             type=ShortReview.TYPE_SHORT_REVIEW)
            sr.save()
    form = WallForm()

    activities = UserActivity.objects.wall_filter(request)

    activities = ajax_activity_pager(request, activities)

    data = {
        'activities': activities,
        'profile': profile,
        'form': form,
        'filter': filter,
    }

    return render(
        request,
        ajax_select_template(request, templates['DASHBOARD']),
        data
    )

@login_required
def my_articles(request):
    """
        List user own articles including drafts.
    """
    user = request.user
    
    articles = Post.objects.all_for_user(user)

    data  = {
        'articles' : articles,
    }

    return render(
        request,
        templates['MY_ARTICLES'],
        data
    )

@login_required
def new_article(request):
    """
       Save new article
    """
    user = request.user

    if request.method == "POST":
        form = BlogPostForm(request.user, request.POST)
        if form.is_valid() == True:
            article = form.save(commit=False)
            article.user = user
            article.slug = slughifi(article.title)
            article.creator_ip = request.META['REMOTE_ADDR']
            article.type = Post.TYPE_POST
            article.temp_related_film = form.cleaned_data['related_film']
            if "save" in request.POST:
                article.status = Post.DRAFT_STATUS
                article.save()
                form.save_m2m()
                request.user.message_set.create(message=_("Successfully saved post '%s'. You have saved the review as draft. If you want to make it visible to others, you need to publish it.") % article.title)
            elif "publish" in request.POST:
                article.status = Post.PUBLIC_STATUS
                article.save()
                form.save_m2m()

                # FLM-1596 save again to use m2m in model
                article.save()

                request.user.message_set.create(message=_("Successfully published post '%s'.") % article.title)
            else:
                raise Http404
            return HttpResponseRedirect("/"+urls.urls["ARTICLES"]+"/")
    else:
        form = BlogPostForm()

    data = {
        'form': form,
    }

    return render(
        request,
        templates['NEW_ARTICLE'],
        data
    )

@login_required
def edit_article(request, id):
    """
       Save edited article
    """
    user = request.user
    article = None
    try:
        article = Post.objects.get(id=id, user=request.user)
    except Post.DoesNotExist:
        raise Http404

    next = request.REQUEST.get( 'next', '' )
    if request.method == "POST":
        form = BlogPostForm(request.user, request.POST, instance=article)
        if form.is_valid() == True:
            article = form.save(commit=False)
            article.user = user
            article.slug = slughifi(article.title)
            article.creator_ip = request.META['REMOTE_ADDR']
            article.type = Post.TYPE_POST
            article.temp_related_film = form.cleaned_data['related_film']

            if "save" in request.POST:
                article.status = Post.DRAFT_STATUS
                article.save()
                request.user.message_set.create(message=_("Successfully saved post '%s'. You have saved the review as draft. If you want to make it visible to others, you need to publish it.") % article.title)
                form.save_m2m()
                article.save_activity()
                return HttpResponseRedirect( next if next else "/"+urls.urls["ARTICLES"]+"/?" + _("drafts") )
            elif "publish" in request.POST:
                article.status = Post.PUBLIC_STATUS
                article.save()
                request.user.message_set.create(message=_("Successfully published post '%s'.") % article.title)
                form.save_m2m()
                article.save_activity()
                return HttpResponseRedirect( next if next else "/"+urls.urls["ARTICLES"]+"/" )

    else:
        new_related_film = []

        def comma_escape(s):
            return s.replace('\\','\\\\').replace(',','\\,')
        
        related_movies = article.related_film.select_related()
        related_people = article.related_person.select_related()
        related_names = ', '.join(comma_escape(unicode(m)) for m in related_people)
        related_film = ', '.join(comma_escape(unicode(m)) for m in related_movies)
        form = BlogPostForm(instance=article, initial={'related_film': related_film, 'related_person':related_names})

    data = {
        'form': form,
        'next': next,
        'article': article,
        'film': article.get_main_related_film()
    }

    return render(
        request,
        templates['EDIT_ARTICLE'],
        data
    )

# ----- Download ratings ---- #
def get_single_review(reviews, filmid):
    quote = ""
    for review in reviews:
        if review.film:
            if review.film.id == filmid:
                quote = review.content
    return quote

def create_data_set(user):
    film = {}
    data_set = []

    recom_helper = RecomHelper()
    ratings = recom_helper.get_all_ratings(user)
    reviews = UserActivity.objects.reviews_for_user(user)

    for rating in ratings:
        filmid = rating.film.id
        filmname = rating.film.title
        filmlink = permalink_film(rating.film)
        img = get_image_path(rating.film, 50, 71)# FLM-1267
        score = rating.rating
        quote = get_single_review(reviews, filmid)
        reviewdate = ""
        if rating.last_rated is not None:
            reviewdate = rating.last_rated.strftime("%b %d %Y, %H:%M")

        film = {
            "filmid": filmid,
            "filmname": filmname,
            "filmlink": filmlink,
            "img": img,
            "score": score,
            "quote": quote,
            "reviewdate": reviewdate,
            "tier": score,
        }
        data_set.append(film)
    return data_set

def output_file(data_set):
    response = HttpResponse(mimetype='text/xml')
    response['Content-Disposition'] = 'attachment; filename=ratings.xml'

    t = loader.get_template(templates["XML_TEMPLATE"])
    c = Context({
        'data_set': data_set
    })
    response.write(t.render(c))
    return response

@login_required
def export_ratings(request, format_as_str=None):
    if format_as_str == 'xml':
        data_set = create_data_set(request.user)
        return output_file(data_set)
    else:
        raise Http404
# ---- End Download ratings ---- #
