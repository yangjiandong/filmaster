# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

# Project
from film20.dashboard.views import *
from film20.userprofile.views import CollectionListView, RatingsListView, \
        ArticlesListView, FollowedListView, FollowersListView, \
        SimilarUsersListView, \
        SimilarUsersFollowingListView, SimilarUsersFollowedListView
from film20.recommendations.urls import genre #

collection_view = login_required(CollectionListView.as_view(template_name = templates['MY_COLLECTION']))
followed_view = login_required(FollowedListView.as_view(template_name = templates['DASHBOARD_FOLLOWED']))
followers_view = login_required(FollowersListView.as_view(template_name = templates['DASHBOARD_FOLLOWERS']))
similar_users_view = login_required(SimilarUsersListView.as_view(template_name = templates['DASHBOARD_SIMILAR_USERS']))
similar_users_following_view = login_required(SimilarUsersFollowingListView.as_view(template_name = templates['DASHBOARD_SIMILAR_USERS']))
similar_users_followed_view = login_required(SimilarUsersFollowedListView.as_view(template_name = templates['DASHBOARD_SIMILAR_USERS']))

dashboardpatterns = patterns('',
    url(r'^'+urls.urls['DASHBOARD']+'/$', show_dashboard, name = 'show_dashboard'),
    url(r'^'+urls.urls['ARTICLES']+'/$', login_required(ArticlesListView.as_view(template_name=templates['MY_ARTICLES'])), name='articles'),
    url(r'^'+urls.urls["NEW_ARTICLE"]+'/$', new_article, name='new_article'),
    url(r'^'+urls.urls["EDIT_ARTICLE"]+'/(?P<id>\d+)/$', edit_article, name='edit_article'),
#    url(r'^'+urls.urls["DELETE_ARTICLE"]+'/(?P<permalink>[\w\-_]+)/$', delete_article), # was: delete-post
    url(r'^'+urls.urls["FOLLOWED"]+'/$', followed_view, name='dashboard_followed'),
    url(r'^'+urls.urls["FOLLOWERS"]+'/$', followers_view, name='dashboard_followers'),
#   revert when http://jira.filmaster.org/browse/FLM-1898 is fixed
#    url(r'^'+urls.urls["SIMILAR_USERS"]+'/$', similar_users_view, name='similar_users_url'),
#    url(r'^'+urls.urls["SIMILAR_USERS_FOLLOWING"]+'/$', similar_users_following_view, name='similar_users_following'),
#    url(r'^'+urls.urls["SIMILAR_USERS_FOLLOWED"]+'/$', similar_users_followed_view, name='similar_users_followed'),
    url(r'^%(WISHLIST)s/$' % urls.urls, collection_view, {'kind':urls.urls['WISHLIST']}, name="wishlist" ),
    url(r'^%(SHITLIST)s/$' % urls.urls, collection_view, {'kind':urls.urls['SHITLIST']}, name="shitlist" ),
    url(r'^%(OWNED)s/$' % urls.urls, collection_view, {'kind':urls.urls['OWNED']}, name="collection" ),
    url(r'^'+urls.urls["RATED_FILMS"]+'/$', login_required(RatingsListView.as_view(template_name = templates['USER_RATED_FILMS'])), name="ratings"),
    url(r'^'+urls.urls["RATED_FILMS"]+'/(?P<type_as_str>[\w\-_]+)/$', login_required(RatingsListView.as_view(template_name = templates['USER_RATED_FILMS'])), name="ratings"),
    url(r'^'+urls.urls["RATED_FILMS"]+'/'+urls.urls["EXPORT_RATINGS"]+'/(?P<format_as_str>[\w\-_]+)/$', export_ratings, name="export_ratings"),
    
    # render wallpost for ajax
    url(r'^ajax/render-wallpost/(?P<id>\d+)/$', 'film20.useractivity.views.render_wallpost', name='render_wallpost'),
    url(r'^ajax/render-comment/(?P<id>\d+)/$', 'film20.useractivity.views.render_comment', name='render_comment'),

)
