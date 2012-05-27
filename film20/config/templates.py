# Templates configuration

templates = {
    # public
    "MAIN": "show_main.html",
    "SHOW_FILM": "show_film.html",
    "SHOW_FILM_FORUM": "comments/film_comments.html",
    "RATE_FILMS": "rate_films.html",
    "RATE_FILMS_FAST_FORWARD": "rate_films_fast.html",
    "SHOW_PERSON": "show_person.html",
    "RANKING": "movies/ranking.html",
    "MOVIES": "movies/base.html",
    "MOVIES_GENRE": "movies/genre.html",
    "MOVIES_REVIEWS": "movies/reviews.html",
    "MOVIES_RECOMMENDATIONS":"movies/recommendations.html",
    "FILMS_FOR_TAG": "tag/tag-films.html",

    "SHOW_TAG_PAGE": "tag.html",

    # search
    "SEARCH": "search/results.html",
    "SEARCH_FILM": "search/search_film.html",
    "SEARCH_PERSON": "search/search_person.html",
    "SEARCH_FORMS": "search/search_forms.html",

    # comments
    "COMMENT_PARTIAL": "comment_partial.html",

    # contest
    "SHOW_GAME": "contest/show_game.html",
    "SHOW_CONTEST": "contest/show_contest.html",
    "SHOW_GAME_AJAX": "contest/show_game_ajax.html",

    # blog
    "ADD_NOTE": "blog/edit_blog_post.html",
    "EDIT_NOTE": "blog/edit_blog_post.html",
    "SHOW_NOTE": "blog/show_blog_post.html",
    "EDIT_BLOG": "blog/edit_blog.html",
    "SHOW_BLOG": "blog/show_blog.html",
    "NOTE_PARTIAL": "blog/note_partial.html",
    # planeta
    "PLANET": "planeta.html",
    "OBJECT_PLANET": "planet/object_planet.html",
    "PLANET_RSS": "planet/planet.xml",
    "RECENT_ANSWERS": "recent_answers.html",
    # private
    "ADD_FRIEND": "add_friend.html", # TODO: remove?
    "MANAGE_INVITATIONS": "manage_invitations.html",
    "HANDLE_INVITATION": "handle_invitation.html",

    #forum
    "FORUM": "forum.html",
    "FORUM_ALL": "forum_all.html",
    "THREAD": "thread.html",
    "EDIT_THREAD": "edit_thread.html",
    "SHOW_EVENT": "event/event.html",
    "SHORT_REVIEW_FORUM": "shortreview_forum.html",
    "LINK_FORUM": "link_forum.html",
    #export xml template
    "XML_TEMPLATE":"movies/rating/xml_template.xml",
    #import films
    "IMPORT_FILMS_RSS":"movies/import_films.xml",
    
    #add films
    "ADD_FILM":"movies/add-movie.html",
    "ADD_FILM_MANUAL":"movies/add-movie-manual.html",

    #add links
    "ADD_LINKS":"externallink/add_link.html",
    "LINK_PARTIAL":"externallink/link_partial.html",

    #follower partial
    "FOLLOWER_PARTIAL":"followers/follower_partial.html",

    #used by mobile landing page
    "REGISTER":"register/mobile.html",

    #dashboard
    "DASHBOARD":"dashboard/base.html",
    "USER_RATED_FILMS":"dashboard/ratings.html",
    "MY_ARTICLES":"dashboard/articles.html",
    "MY_COLLECTION":"dashboard/collection.html",
    "NEW_ARTICLE":"dashboard/new_article.html",
    "EDIT_ARTICLE":"dashboard/edit_article.html",
    "DASHBOARD_FOLLOWED":"dashboard/followed.html",
    "DASHBOARD_FOLLOWERS":"dashboard/followers.html",
    "DASHBOARD_SIMILAR_USERS":"dashboard/similar_users.html",

    #profile
    "PROFILE":"profile/base.html",
    "PROFILE_RATED_FILMS":"profile/ratings.html",
    "PROFILE_COLLECTION":"profile/collection.html",
    "WALL_POST":"profile/wall_post.html",
    "PROFILE_FOLLOWED":"profile/followed.html",
    "PROFILE_FOLLOWERS":"profile/followers.html",
    "PROFILE_SIMILAR_USERS":"profile/similar_users.html",
    "ARTICLE":"profile/article.html",

    #settings
    "USER_SETTINGS": "usersettings/usersettings.html",
    "EDIT_NOTIFICATION_SETTINGS": "usersettings/edit_notification_settings.html",
    "IMPORT_RATINGS_SETTINGS": "usersettings/import_ratings.html",
    "IMPORT_RATINGS_SUMMARY_SETTINGS": "usersettings/import_summary.html",
}
