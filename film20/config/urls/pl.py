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

success = "sukces"
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
    "BLOG_POST_OLD": "notka",
    "SHORT_REVIEW_OLD": "krotka-recenzja",

    ### PUBLIC ###
    
    "FIRST_TIME_INFO": "pierwsze-kroki",
    "FAQ": "faq",
    
    "MAIN": "",
    "ADMIN": "admin",    
    "FILM": "film",
    "TV_SERIES": "serial",
    "TV_SERIES_RANKING": "rankingi-seriali",
    "RATE_FILMS": "oceniaj-filmy",
    "RATE_FILMS_FAST_FORWARD": "oceniarka",
    "RATE_NEXT": "ocen-nastepny",
    "PERSON": "osoba",
    "SEARCH": "szukaj",
    "SEARCH_FILM": "szukaj-filmu",
    "SEARCH_PERSON": "szukaj-osoby",
    "BLOG": "blog",
    "ARTICLE": "artykul",
    "CHECKIN": "checkin",
    "ARTICLES":"artykuly",
    "ARTICLES_OLD":"notki",
    "PLANET": "planeta",
    "RECENT_ANSWERS": "odpowiedzi",
    "PLANET_FOLLOWED": "planeta/obserwowani",
    "POSTER": "plakat",
    
    # kokpit
    "DASHBOARD": "kokpit",
    
    # publiczne profile
    "SHOW_PROFILE": "profil",
    "LIST_PROFILES": "lista-profili", #TODO: is this required?
    "USER_ARTICLES": "artykuly-filmastera", #TODO: is this required?

    "FILMS": "filmy",
    "AGENDA": "agenda",
    
    # ogolne do wykorzystania w linkach
    "RATING": "ocena",
    "EDIT": "edytuj",
    "PREVIOUS": "poprzedni",
    "NEXT": "nastepny",
    "FEED": "feed",

    "FILMS_FOR_TAG": "filmy",
    "RANKING": "rankingi",
    "FESTIVAL_RANKING": "ranking",
    "RATINGS": "oceny",
    "RECOMMENDATIONS": "rekomendacje",
    "COMPUTE": "przelicz",
    "TOP_USERS": "filmasterzy",
    "FOLLOWED": "obserwowani",
    "FOLLOWERS": "obserwujacy",
    "SIMILAR_USERS": "podobni-uzytkownicy",
    "SIMILAR_USERS_FOLLOWING": "podobni-uzytkownicy-obserwowani",
    "SIMILAR_USERS_FOLLOWED": "podobni-uzytkownicy-obserwujacy",
#    "COMPUTE_PROBABLE_SCORES": "wylicz-rekomendacje",
    
    "FILMBASKET": "koszyk",
    "OWNED": "kolekcja",
    "WISHLIST": "wishlista",
    "SHITLIST": "shitlista",

    "TAG": "tag",
    "SHOW_TAG_PAGE": "tag",
    
    "ADD_TO_BASKET": "dodaj-do-koszyka",

    "REGIONAL_INFO": "informacje-regionalne",
    
    "AJAX": "ajax",
    # strony statyczne (TODO: zastapic flatpages?)
    "TERMS": "regulamin",
    "PRIVACY": "prywatnosc",
    "LICENSE": "licencja",
    "CONTACT": "kontakt",
    "ABOUT": "redakcja",
    "COOPERATION": "wspolpraca",
    "BANNERS": "banery",
    "ADVERTISEMENT": "reklama",
    "AVATAR_HOWTO": "awatar-howto",
    "FORMATTING_POSTS": "formatowanie",
        
    ### PRIVATE ###
    
    # logowanie i rejestracja
    "ACCOUNT": "dashboard",    

    "OPENID_ASSOCIATIONS": "openid/associations",
    "ASSIGN_FACEBOOK":"fb/assign_facebook",
    "EDIT_FACEBOOK":"fb/edit",
    
    "LOGIN": "konto/login",
    "LOGOUT": "konto/logout",
    "CHANGE_PASSWORD": "zmien-haslo",
    "RESET_PASSWORD": "konto/reset-hasla",
    "RESET_PASSWORD_CONFIRM": "konto/reset-hasla/potwierdzenie",
    "RESET_PASSWORD_COMPLETE": "konto/reset-hasla/koniec",
    "RESET_PASSWORD_DONE": "konto/reset-hasla/sukces",
    
    "REGISTRATION": "konto/rejestracja",
    "REGISTRATION_ACTIVATE": "konto/rejestracja/aktywacja",
    "REGISTRATION_COMPLETE": "konto/rejestracja/koniec",    
    
    "ASSOCIATIONS": "edytuj-powiazane-serwisy",
    "OAUTH_LOGIN": "konto/oauth-login",
    "OAUTH_LOGIN_CB": "konto/oauth-login-cb",
    "OAUTH_NEW_USER": "konto/oauth/nowy",
    
    # friends and invitations
    "MANAGE_INVITATIONS": "konto/zaproszenia",
    "ACCEPT_INVITATION": "konto/akceptuj-zaproszenie",
    "REFUSE_INVITATION": "konto/odrzuc-zaproszenie",

    # old notifications - TODO: remove
    "NOTIFICATIONS": "konto/powiadomienia",
    "NOTIFICATION": "konto/powiadomienia/powiadomienie",
    "MARK_NOTIFICATIONS_AS_READ": "konto/powiadomienia/oznacz-jako-przeczytane",

    "DASHBOARD_SETTINGS": "konto/ustawienia_kokpitu",
    
    "PW": "pw",
    "PW_INBOX": "odebrane",
    "PW_OUTBOX": "wyslane",
    "PW_COMPOSE": "stworz",
    "PW_REPLY": "odpowiedz",
    "PW_VIEW": "zobacz",
    "PW_DELETE": "usun",
    "PW_CONV_DELETE": "usun-watek",
    "PW_CONV_VIEW": "zobacz-watek",
    "PW_UNDELETE": "przywroc",
    "PW_TRASH": "kosz",
    
    #export
    "EXPORT_RATINGS":"pobierz",

    # profiles
    "CREATE_PROFILE": "konto/stworz-profil",
    "EDIT_PROFILE": "konto/edytuj-profil",
    "EDIT_PROFILE_DONE": "konto/edytuj-profil/sukces",
    "EDIT_LOCATION": "edytuj-lokalizacje",
    "DELETE_PROFILE": "konto/usun-profil",
    "DELETE_PROFILE_DONE": "konto/usun-profil/sukces",

    "EDIT_AVATAR": "konto/edytuj-awatar",
    "CROP_AVATAR": "konto/wytnij-awatar",
    "DELETE_AVATAR": "konto/usun-awatar",
    
    # forum
    "FORUM": "forum",
    "FORUM_FILMASTER": "forum/forum-filmastera",
    "FORUM_HYDE_PARK": "forum/hyde-park",
    "EDIT_COMMENT": "edytuj-komentarz",
    # user activities
    "COMMENTS": "komentarze",
    "REVIEWS": "recenzje",
    "REVIEW": "recenzja",
    "SHORT_REVIEWS": "krotkie-recenzje",
    "SHORT_REVIEW": "krotka-recenzja",
    
    # default poster
    "DEFAULT_POSTER": "/static/img/default_poster.png",
    "DEFAULT_ACTOR": "/static/img/default_actor.png",

    #rss
    "RSS": "rss",

    # special events
    "SHOW_EVENT": "wydarzenia",
    "SHOW_FESTIVAL": "festiwal",
    "ORIGINAL_TITLE": "tytul-oryginalny",

    # contest
    "SHOW_GAME": "mecz",
    "SHOW_CONTEST": "plebiscyt",
    "CONTEST_VOTE_AJAX": "vote_ajax",

    # add films
    "ADD_FILMS":"dodaj-film",
    "EDIT_CAST":"edytuj-obsade",
    
    #add links
    "ADD_LINKS":"dodaj-link",
    "REMOVE_LINKS":"usun-link",
    "ADD_VIDEO":"dodaj-video",
    "LINKS":"linki",
    "LINK":"link",

    #nudge button
    "NUDGE":"szturchnij",

    #follow
    "FOLLOW":"obserwuj",

    #delete comment
    "DELETE_COMMENT":"usun-komentarz",
    
    #moderated photos
    "POSTER_ADD":"dodaj-plakat",
    "PHOTO_ADD":"dodaj-zdjecie",
    "MODERATED_PHOTOS": "plakaty-i-zdjecia",

    #moderated films
    "MODERATED_FILMS": "filmy",

    "MOVIES": "filmy",
    "GENRE": "gatunek",


    #mobile landing page
    "MOBILE":"mobile",

    #content moderation
    "MODERATION": "moderacja",

    #wall
    "WALL":"wall",

    #settings
    "SETTINGS": "ustawienia",
    "MANAGE_NOTIFICATIONS": "zarzadzaj-powiadomieniami",
    "IMPORT_RATINGS":"importuj-oceny",

    #dashboard
    "NEW_ARTICLE":"nowy-artykul",
    "EDIT_ARTICLE":"edytuj-artykul",
    "RATED_FILMS":"oceny",

    #showtimes
    "SHOWTIMES": "rekomendacje",
    "SCREENING": "seanse",
    "CINEMAS": "kina",
    "CINEMA": "kino",
    "CHANNEL": "kanal",
    "THEATERS": "kina",
    "THEATER": "kino",
    "TV": "tv",
    "TV_CHANNELS": "kanaly-tv",
    
    # applications
    "APPLICATIONS": "aplikacje",
    "APPLICATION": "aplikacja",
    "ADD_APPLICATION": "dodaj-aplikacje",
    "REMOVE_ACCESS_TOKEN": "usun-token",
    "REMOVE_APPLICATION": "usun-aplikacje",

    # demots
    "DEMOT": "demot",
    "DEMOTS": "filmowe-demoty",
    "DEMOTS_ADD": "filmowe-demoty/dodaj",
}
