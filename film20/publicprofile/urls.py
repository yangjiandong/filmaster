from django.conf.urls.defaults import *

from film20.publicprofile.views import *
from film20.threadedcomments.views import comment
from film20.userprofile.views import CollectionListView, RatingsListView, \
        ArticlesListView, FollowedListView, FollowersListView, \
        SimilarUsersListView, SimilarUsersFollowingListView, SimilarUsersFollowedListView, \
        ArticlesRSS, UserRecommendationsView

from film20.usersubdomain.sitemap import sitemappatterns

collection_view = (CollectionListView.as_view(template_name = templates['PROFILE_COLLECTION']))
articles_view = (ArticlesListView.as_view(template_name=templates['PROFILE']))
articles_rss = ArticlesRSS()
ratings_view = (RatingsListView.as_view(template_name = templates['PROFILE_RATED_FILMS']))
followed_view = (FollowedListView.as_view(template_name = templates['PROFILE_FOLLOWED']))
followers_view = (FollowersListView.as_view(template_name = templates['PROFILE_FOLLOWERS']))
similar_users_view = SimilarUsersListView.as_view(template_name = templates['PROFILE_SIMILAR_USERS'])
similar_users_following_view = SimilarUsersFollowingListView.as_view(template_name = templates['PROFILE_SIMILAR_USERS'])
similar_users_followed_view = SimilarUsersFollowedListView.as_view(template_name = templates['PROFILE_SIMILAR_USERS'])
user_recommendations_view = UserRecommendationsView.as_view()

urlpatterns = patterns('',
    url(r'^$', public_profile, {'activity_option': 'user_all'}, name="show_profile"),
    url(r'^' + urls['ARTICLE'] + '/(?P<permalink>[\w\-_]+)/$', show_article, name='show_article'),
    url(r'^' + urls['CHECKIN'] + '/(?P<id>\d+)/$', show_checkin, name='show_checkin'),
    url(r'^' + urls['RATING'] + '/(?P<id>\d+)/$', show_rating, name='show_rating'),
    url(r'^' + urls['LINK'] + '/(?P<id>\d+)/$', show_link, name='show_link'),
    url(r'^' + urls['POSTER'] + '/(?P<id>\d+)/$', show_poster, name='show_poster'),
    url(r'^trailer/(?P<id>\d+)/$', show_trailer, name='show_trailer'),
    url(r'^' + urls['DEMOT'] + '/(?P<id>\d+)/$', show_demot, name='show_demot'),
    url(r'^'+urls['ARTICLES_OLD'] + '/$', articles_view, name='articles'),
    url(r'^'+urls['ARTICLES'] + '/$', articles_view, name='articles'),
    # rss
    url(r'^'+ 'feed/$', articles_rss, name='articles_rss'),
    url(r'^'+ 'rss/$', articles_rss ),

    url(r'^'+urls['WALL']+'/(?P<post_id>\d{1,10})/$', show_wall_post, name='show_wall_post'),
    url(r'^'+urls['FOLLOWED']+'/$', followed_view, name='profile_followed'),
    url(r'^'+urls['FOLLOWERS']+'/$', followers_view, name='profile_followers'),

    url(r'^'+urls['WISHLIST']+'/$', collection_view, {'kind':urls['WISHLIST']}, name="wishlist" ),
    url(r'^'+urls['SHITLIST']+'/$', collection_view, {'kind':urls['SHITLIST']}, name="shitlist" ),
    url(r'^'+urls['OWNED']+'/$', collection_view, {'kind':urls['OWNED']}, name="collection" ),

    url(r'^'+urls['RATED_FILMS']+'/$', ratings_view, name='ratings'),
    url(r'^'+urls['RATED_FILMS']+'/(?P<type_as_str>[\w\-_]+)/$', ratings_view, name="ratings"),

    url(r'^'+urls["RECOMMENDATIONS"]+'/$', user_recommendations_view, name='user_recommendations'),

#   revert when http://jira.filmaster.org/browse/FLM-1898 is fixed
#    url(r'^'+urls["SIMILAR_USERS"]+'/$', similar_users_view, name='profile_similar_users_url'),
#    url(r'^'+urls["SIMILAR_USERS_FOLLOWING"]+'/$', similar_users_following_view, name='profile_similar_users_following'),
#    url(r'^'+urls["SIMILAR_USERS_FOLLOWED"]+'/$', similar_users_followed_view, name='profile_similar_users_followed'),
) + sitemappatterns

