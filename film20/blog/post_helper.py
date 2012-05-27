from film20.blog.models import Post, Blog
from django.utils.translation import gettext_lazy as _
from film20.utils.slughifi import slughifi
from film20.utils import cache_helper as cache
from film20.blog.models import Post

def save_shortreview_as_post(shortreview, object, user):

    blogs = Blog.objects.select_related().get_or_create(user=user)
    blog = blogs[0]
    title = object.get_localized_title()
    if not title : title = object.title
    post = Post(title = _('Review') + ": " + title,\
                body = shortreview, author = blog,\
                permalink = slughifi(title + " " + " ".join((shortreview.split(' ')[:9])))[:128],\
                type = Post.TYPE_POST,\
                status = Post.PUBLIC_STATUS)
    post.save()
    post.related_film.add(object)
    return post

def get_related_posts(activity, user, number_of_posts=5):
    """ Returns related posts to a given article activity """

    if activity.film:
        related_posts = Post.objects.select_related()\
                .filter(related_film=activity.film,
                        status=Post.PUBLIC_STATUS)\
                .exclude(id=activity.post.id)[:number_of_posts]
    else:
        related_posts = Post.objects.select_related()\
                .filter(user=user,
                status=Post.PUBLIC_STATUS)\
                .exclude(id=activity.post.id)[:number_of_posts]

    if not related_posts.count():
        related_posts = None

    return related_posts

