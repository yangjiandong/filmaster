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
# Project
from film20.config.templates import templates

success = "success"
error = "error"

def full_url(key):
    try:
        from django.conf import settings
        DOMAIN = settings.DOMAIN
        FULL_DOMAIN = settings.FULL_DOMAIN
    except:
        DOMAIN = ''
        FULL_DOMAIN = ''
    return (FULL_DOMAIN or DOMAIN) + '/'+urls[key]+'/'

urls = {
    ### LEGACY STUFF FOR COMPATIBILITY: FLM-1185 ###
    "BLOG_POST_OLD": "review",
    "SHORT_REVIEW_OLD": "short-review",

    ### PUBLIC ###

    "FIRST_TIME_INFO": "first-steps",
    "FAQ": "faq",

    "MAIN": "",
    "ADMIN": "admin",
    "FILM": "film",
    "TV_SERIES": "series",
    "TV_SERIES_RANKING": "series-ranking",
    "RATE_FILMS": "rate-movies",
    "RATE_FILMS_FAST_FORWARD": "rater",
    "RATE_NEXT": "rate-next",
    "PERSON": "person",
    "SEARCH": "search",
    "SEARCH_FILM": "search-film",
    "SEARCH_PERSON": "search-person",
    "BLOG": "blog",
    "ARTICLE": "article",
    "CHECKIN": "checkin",
    "ARTICLES":"articles",
    "ARTICLES_OLD":"reviews",
    "POSTER": "poster",

    # dashboard
    "DASHBOARD": "dashboard",

    # publiczne profile
    "SHOW_PROFILE": "profile",
    "LIST_PROFILES": "list-profiles",
    "USER_ARTICLES":"user-articles",

    "FILMS": "films",
    "AGENDA": "agenda",

    # ogolne do wykorzystania w linkach
    "RATING": "rate",
    "EDIT": "edit",
    "PREVIOUS": "previous",
    "NEXT": "next",
    "FEED": "feed",

    "FILMS_FOR_TAG": "films",
    "RANKING": "rankings",
    "FESTIVAL_RANKING": "ranking",
    "RATINGS": "ratings",
    "RECOMMENDATIONS": "recommendations",
    "COMPUTE": "compute",
    "TOP_USERS": "filmasters",
    "FOLLOWED": "followed",
    "FOLLOWERS": "followers",
    "SIMILAR_USERS": "similar-users",
    "SIMILAR_USERS_FOLLOWING": "similar-users-following",
    "SIMILAR_USERS_FOLLOWED": "similar-users-followed",
#    "COMPUTE_PROBABLE_SCORES": "wylicz-rekomendacje",

    "FILMBASKET": "basket",
    "OWNED": "collection",
    "WISHLIST": "wishlist",
    "SHITLIST": "shitlist",

    "TAG": "tag",
    "SHOW_TAG_PAGE": "tag",

    "ADD_TO_BASKET": "add-to-basket",

    "REGIONAL_INFO": "regional-info",

    "AJAX": "ajax",
    # strony statyczne
    "TERMS": "terms-of-use",
    "PRIVACY": "privacy",
    "LICENSE": "license",
    "CONTACT": "contact",
    "ABOUT": "about",
    "COOPERATION": "cooperation",
    "BANNERS": "banners",
    "ADVERTISEMENT": "advertisement",
    "AVATAR_HOWTO": "avatar-howto",
    "FORMATTING_POSTS": "formatting",

    ### PRIVATE ###

    # logowanie i register
    "ACCOUNT": "dashboard",

    "OPENID_ASSOCIATIONS": "openid/associations",
    "ASSIGN_FACEBOOK":"fb/assign_facebook",
    "EDIT_FACEBOOK":"fb/edit",

    "LOGIN": "account/login",
    "LOGOUT": "account/logout",
    "CHANGE_PASSWORD": "change-password",
    "RESET_PASSWORD": "account/reset-password",
    "RESET_PASSWORD_CONFIRM": "account/reset-password/confirm",
    "RESET_PASSWORD_COMPLETE": "account/reset-password/finish",
    "RESET_PASSWORD_DONE": "account/reset-hasla/success",

    "REGISTRATION": "account/register",
    "REGISTRATION_ACTIVATE": "account/register/activate",
    "REGISTRATION_COMPLETE": "account/register/finish",

    "ASSOCIATIONS": "edit-connected-services",
    "OAUTH_LOGIN": "account/oauth-login",
    "OAUTH_LOGIN_CB": "account/oauth-login-cb",
    "OAUTH_NEW_USER": "account/oauth/new",

    # friends and invitations
    "MANAGE_INVITATIONS": "account/invitations",
    "ACCEPT_INVITATION": "account/accept-invitation",
    "REFUSE_INVITATION": "account/reject-invitation",

    # old notifications - TODO: remove
    "NOTIFICATIONS": "account/notifications",
    "NOTIFICATION": "account/notifications/notice",
    "MARK_NOTIFICATIONS_AS_READ": "account/notifications/mark-as-read",

    "DASHBOARD_SETTINGS": "account/dashboard_settings",

    "PW": "pm",
    "PW_INBOX": "received",
    "PW_OUTBOX": "sent",
    "PW_COMPOSE": "compose",
    "PW_REPLY": "reply",
    "PW_VIEW": "view",
    "PW_DELETE": "delete",
    "PW_CONV_DELETE": "delete-thread",
    "PW_CONV_VIEW": "view-thread",
    "PW_UNDELETE": "undelete",
    "PW_TRASH": "trash",

    # notes
    "ADD_NOTE": "account/write-review",
    "EDIT_NOTE": "account/edit-reviews",
    "DELETE_NOTE": "account/delete-review",
    "NOTE_PARTIAL":"note-partial",

    #export
    "EXPORT_RATINGS":"download",

    # profiles
    "CREATE_PROFILE": "account/create-profile",
    "EDIT_PROFILE": "account/edit-profile",
    "EDIT_PROFILE_DONE": "account/edit-profile/success",
    "EDIT_LOCATION": "edit-location",
    "DELETE_PROFILE": "account/delete-profile",
    "DELETE_PROFILE_DONE": "account/delete-profile/success",

    "EDIT_AVATAR": "account/edit-avatar",
    "CROP_AVATAR": "account/crop-avatar",
    "DELETE_AVATAR": "account/delete-awatar",

    # forum
    "FORUM": "forum",
    "FORUM_FILMASTER": "forum/filmaster-forum",
    "FORUM_HYDE_PARK": "forum/hyde-park",
    "EDIT_COMMENT": "edit-comment",
    # user activities
    "COMMENTS": "comments",
    "REVIEWS": "reviews",
    "REVIEW": "review",
    "SHORT_REVIEWS": "short-reviews",
    "SHORT_REVIEW": "short-review",

    # default poster
    "DEFAULT_POSTER": "/static/img/default_poster.png",
    "DEFAULT_ACTOR": "/static/img/default_actor.png",

    #rss
    "RSS": "rss",

    # special events
    "SHOW_EVENT": "events",
    "SHOW_FESTIVAL": "festival",
    "ORIGINAL_TITLE": "original-title",

    # contest
    "SHOW_GAME": "game",
    "SHOW_CONTEST": "contest",
    "CONTEST_VOTE_AJAX": "vote_ajax",

    # add films
    "ADD_FILMS":"add-films",
    "EDIT_CAST":"edit-cast",

    #add links
    "ADD_LINKS":"add-link",
    "REMOVE_LINKS":"remove-link",
    "ADD_VIDEO":"add-video",
    "LINKS":"links",
    "LINK":"link",

    #nudge button
    "NUDGE":"nudge",

    #follow
    "FOLLOW":"follow",

    #delete comment
    "DELETE_COMMENT":"delete-comment",

    #moderated photos
    "POSTER_ADD": "poster-add",
    "PHOTO_ADD": "photo-add",
    "MODERATED_PHOTOS": "posters-and-photos",

    #moderated films
    "MODERATED_FILMS": "movies",

    "MOVIES": "movies",
    "GENRE": "genre",

    #mobile landing page
    "MOBILE":"mobile",

    #content moderation
    "MODERATION": "moderation",

    #wall
    "WALL":"wall",

    #settings
    "SETTINGS": "settings",
    "MANAGE_NOTIFICATIONS": "manage-notifications",
    "IMPORT_RATINGS":"import-ratings",

    #dashboard
    "NEW_ARTICLE":"new-article",
    "EDIT_ARTICLE":"edit-article",
    "RATED_FILMS":"ratings",

    #showtimes
    "SHOWTIMES": "recommendations",
    "SCREENING": "screening",
    "CINEMAS": "cinemas",
    "CINEMA": "cinema",
    "CHANNEL": "channel",
    "THEATERS": "theaters",
    "THEATER": "theater",
    "TV": "tv",
    "TV_CHANNELS": "tv-channels",

    # applications
    "APPLICATIONS": "application",
    "APPLICATION": "application",
    "ADD_APPLICATION": "add-application",
    "REMOVE_ACCESS_TOKEN": "remove-access-token",
    "REMOVE_APPLICATION": "remove-application",

    # demots
    "DEMOT": "demot",
    "DEMOTS": "movie-demots",
    "DEMOTS_ADD": "movie-demots/add",
}
