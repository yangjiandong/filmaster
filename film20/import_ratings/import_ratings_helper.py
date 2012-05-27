#-*- coding: utf-8 -*-
#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------
# Python
import re
import csv
import cookielib
import urllib
import urllib2
import mechanize
import time
import logging
from haystack.query import SearchQuerySet
from haystack.backends import SQ
from urllib2 import urlopen as _urlopen
from xml.dom import minidom
from datetime import datetime
from BeautifulSoup import BeautifulSoup

# Django
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.utils import simplejson as json

# Project
from film20.core.models import Rating, ShortReview, Film, FilmLocalized, Object
from film20.import_ratings.models import ImportRatings, ImportRatingsLog,\
                                         save_ratings_in_db
from film20.import_films.models import ImportedFilm, FilmToImport
from film20.import_films import imdb_fetcher
from film20.search import search_film as global_search_film
from film20.utils.slughifi import slughifi
from film20.core import rating_helper
from django.conf import settings

LANGUAGE_CODE = settings.LANGUAGE_CODE
NUMBER_OF_ATTEMPTS = getattr(settings, "NUMBER_OF_ATTEMPTS", 3)
logger = logging.getLogger(__name__)

SCORE_TIER = 'tier'
SCORE_EXACT = 'score'
SCORE_AUTO = 'auto'
SCORE_DIV10 = 'score/10'
SCORE_CONVERTIONS = (
    (SCORE_TIER, _('tier - If you rate things normally on Criticker, choose TIER. This will give a rating on Filmaster based on the tier on Criticker.')),
    (SCORE_EXACT, _('exact - Exact score works only if you rate films on Criticker in 0-10 scale.')),
    (SCORE_DIV10, _('score/10 - If you rate very few bad films, and use the whole criticker scale (0-100) choose /10 - this simply divides the criticker score by 10.')),
    (SCORE_AUTO, _('auto - Auto uses tier.')),
)

DEBUG = True


def escape_text(text):
    return text.replace('&', '&amp;')


def parse_criticker_votes(xml_file=None, score_convertion=SCORE_AUTO,
                          import_reviews=False):
    """
        Parses a file in Criticker XML format and returns a list of ratings
    """
    all_ratings = []
    if xml_file:
        DOMTree = minidom.parse(xml_file)
    else:
        logger.errror("Parsing criticker votes failed. Please provide either an xml_file or xml_string in parameters!")
        return None

    year_pattern = re.compile(".\((\d{4})\)")

    nodes = DOMTree.childNodes
    min = max = None
    for i in nodes[0].getElementsByTagName('score'):
        score = int(i.childNodes[0].data)
        if not max or score > max:
            max = score
        if not min or score < min:
            min = score
    span = max - min
    if span == 0:
        span = 100

    for film in nodes[0].getElementsByTagName("film"):
        film_title = escape_text(film.getElementsByTagName("filmname")[0].
                                 childNodes[0].data)

        tier = int(film.getElementsByTagName("tier")[0].childNodes[0].data)
        score = int(film.getElementsByTagName("score")[0].childNodes[0].data)

        scores = {SCORE_TIER: tier,
                  SCORE_AUTO: int(round(float(score - min) / (span) * 9 + 1)),
                  SCORE_DIV10: int(round(float(score) / 10)),
                  SCORE_EXACT: score}
        score = scores[score_convertion]
        if score < 1:
            score = 1
        elif score > 10:
            score = 10

        title = year_pattern.sub('', film_title)
        movie = {'title': title, 'score': score}

        fetch_year = year_pattern.search(film_title)
        try:
            year = int(fetch_year.groups(0)[0])
            movie['year'] = year
        except:
            pass

        filmid = film.getElementsByTagName("filmid")[0].childNodes[0].data
        movie['criticker_id'] = filmid

        if import_reviews:
            review = None
            review = escape_text(film.getElementsByTagName("quote")[0].
                                 childNodes[0].data)
            if review:
                movie['review'] = review

        all_ratings.append(movie)
    return all_ratings


def parse_imdb_votes(csv_file):
    """
    Parse IMDB votes from CSV
    """
    all_ratings = []
    movie = None

    reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
    for row in reader:
        id = row['const']
        id = id[2:]
        title = row['Title']
        year = row['Year']
        score = row['You rated']
        movie = {'imdb_id': id, 'title': title, 'score': int(score)}
        try:
            movie['year'] = int( year )
        except ValueError, e:
            logger.debug( 'Cannot parse year: %s' % e )

        all_ratings.append(movie)
    return all_ratings


def fetch_film_info_from_criticker(film_data):
    url = 'http://www.criticker.com/?f=' + film_data['criticker_id']
    logger.info("Fetch info from %s" % url)
    title_page = None
    try:
        page = unicode(_urlopen(url, None, 5).read(), 'iso-8859-1')
        soup = BeautifulSoup(page)
        title_page = soup.find("div", attrs={"id": "fi_info_filmname"})
    except urllib2.URLError, e:
        logger.error("URL Error: " + str(e.reason) + ": " + url)

    if title_page:
        full_title = title_page.contents[0]
        title = full_title.split("&nbsp;")
        title = title[0]

        akas_page = soup.findAll("div", attrs={"id": "fi_info_akas"})
        akas = []
        if akas_page:
            for aka in akas_page:
                alt_title = aka.contents[1].lstrip()
                akas.append(alt_title)
            akas.append(title)
        else:
            akas = None

        year_page = re.compile(".*\((\d{4})\)")
        fetch_year = re.match(year_page, full_title)
        year = int(fetch_year.groups(0)[0])

        film_data['imdb_id'] = ''

        imdb_page = soup.find("div", attrs={"id": "fi_info_imdb"})
        if imdb_page:
            imdb_url = soup.find("a", attrs={"target": "imdbwin"})
            imdb_regex = re.compile("\d{7}")
            imdb_id = re.findall(imdb_regex, str(imdb_url))[0]
            film_data['imdb_id'] = imdb_id

        film_data['year'] = year
        film_data['aka'] = akas
        film_data['title'] = title
        if not year:
            try:
                logger.warning("Couldn't find year for %s (%s)" %
                                (title.encode('utf-8'), str(url)))
            except:
                logger.warning("Couldn't find year for a film. Exception when trying to print its title! Criticker ID: %s" %
                 (str(film_data['criticker_id'])))
    else:
        film_data['year'] = film_data['year'] if 'year' in film_data else None
        film_data['title'] = film_data['title'] if 'title' in film_data else None
        film_data['aka'] = None
        film_data['imdb_id'] = None
        logger.debug("Film %s doesn't exist on Criticker" % film_data['title'])


def search_film(film_title=None, year=None, imdb_id=None, criticker_id=None,
                filmweb_id=None):
    """
        Search for a film while importing ratings
    """
    from film20.utils.texts import normalized_text
    title_normalized = normalized_text(film_title)

    if imdb_id:
        try:
            film = Film.objects.get(imdb_code=imdb_id)
            if normalized_text(film.title) == title_normalized and (not year or
                                                                    year == film.release_year):
                return film
            else:
                logger.debug("WARN: not matching film! searching for: #%s %s (%s); found %s (%s)" % (imdb_id,
                                                    film_title.encode('utf-8'),
                                                    year, film.title.encode('utf-8'),
                                                    film.release_year))
                # fix for http://jira.filmaster.org/browse/FLM-491
                # fetch movie by this imdb_code and check if year is same
                #   and title is in akas then return this film
                movie = imdb_fetcher.get_movie_by_id(imdb_id, "http")
                if movie:
                    if movie.get('year') == year:
                        akas = movie.get('akas')
                        for aka in akas:
                            t, c = aka.split('::')
                            if t == film_title:
                                logger.info(" -- title is: %s" % c)
                                return film
                    else:
                        logger.error("ERROR: this imdb_code is probably wrong ...")

        except Exception, e:
            logger.error("ERROR: %s" % e)
    if criticker_id:
        try:
            return Film.objects.get(criticker_id=str(criticker_id))
        except:
            pass

    all_results = global_search_film( film_title )
   
    if year:
        all_results = [f for f in all_results if f.release_year == year]
        #print "new all results for %s (%s): %s" % (film_title, year, ["%s (%s)" % (f.title, f.release_year) for f in all_results])
    exact, normalized, fuzzy = [], [], []

    def filter_films():
        for film in all_results:
            e = n = f = False
            if film.title.lower() == title_lower:
                exact.append(film)
                e = True
            norm = normalized_text(film.title)
            if norm == title_normalized:
                normalized.append(film)
                n = True
            #if norm.startswith(title_normalized) or title_normalized.startswith(norm):
            if norm in title_normalized or title_normalized in norm:
                fuzzy.append(film)
                f = True
            if not e:
                for l in FilmLocalized.objects.filter(film=film.id):
                    if not e and l.title.lower() == title_lower:
                        exact.append(film)
                        e = True
                    norm = normalized_text(l.title)
                    if not n and norm == title_normalized:
                        normalized.append(film)
                        n = True
                    #if not f and (norm.startswith(title_normalized) or title_normalized.startswith(norm)):
                    if not f and (norm in title_normalized or title_normalized in norm):
                        fuzzy.append(film)
                        f = True
    filter_films()

    if len(exact) == 1:
        return exact[0]
    if len(normalized) == 1:
        return normalized[0]
    #if year and len(fuzzy)==1:
    #    try:
    #        print "INFO: returning fuzzy match for %s (%s): %s (%s)" % (film_title, year, fuzzy[0].title, fuzzy[0].release_year)
    #    except UnicodeEncodeError:
    #        print "INFO: fuzzy match for %s(imdb) %s(criticker) (and unicode encode error problem!)" % (imdb_code, criticker_id)
    #    return fuzzy[0]
    #if not normalized and len(all_results)==1:
    #    return all_results[0]
    if year:
        all_results = [f for f in all_results if abs(f.release_year - int(year)) <= 1]
        filter_films()
        if len(exact) == 1:
            return exact[0]
        if len(normalized) == 1:
            return normalized[0]
    return None


def save_ratings_db(user, ratings, kind, overwrite=False):
    films = json.dumps(ratings)

    ratings = ImportRatings(movies=films, user=user, overwrite=overwrite,
                            kind=kind)
    ratings.save()


def save_rating(film, user, score=None, review=None, overwrite=False):
    """
        Saves a single rating to database
    """
    rated = False
    if score:
        score = int(float(score))
        link = film.parent.permalink
        rated = rating_helper.rate(user, score, film_id=film.id, overwrite=overwrite, check_if_exists=True, _send_notice=False)

    if review and len(review) < ShortReview._meta.get_field('review_text').max_length:
        try:
            sr = ShortReview.all_objects.get(kind=ShortReview.REVIEW,
                                             object=film, user=user,
                                             LANG=settings.LANGUAGE_CODE)
            logger.info("review fetched from db: updating for user_id %s, object %s" % (str(user.id), str(film.id)))
        except ShortReview.DoesNotExist:
            sr = ShortReview(type=ShortReview.TYPE_SHORT_REVIEW,
                             kind=ShortReview.REVIEW, permalink='FIXME',
                             status=1, version=1, object=film, user=user,
                             LANG=settings.LANGUAGE_CODE)
            logger.info("review doesn't exist, creating with user_id: %s, object %s" % (str(user.id), str(film.id)))

        if not sr.review_text or overwrite:
            sr.review_text = review
            try:
                sr.save()
                logger.info("review saved")
            except Exception, e:
                logger.error("review not saved, exception caught: " + str(e))

    return rated


def save_ratings(user, ratings, overwrite):
    """
        Saves a list of imported ratings for the selected user
    """
    movies_rated_list = []
    movies_already_rated_list = []
    titles_rated = []
    titles_already_rated = []
    titles_not_rated = []
    f = lambda title, year: title if not year else title + " (%s)" % str(year)

    def rate_film(film, film_title, year, score, review, overwrite):
        was_rated = save_rating(film, user, score, review, overwrite)
        if was_rated:
            movies_already_rated_list.append(film)
            titles_already_rated.append(f(film_title, year))
        if overwrite or not was_rated:
            movies_rated_list.append(film)
            titles_rated.append(f(film_title, year))

    for record in ratings:
        film_title = record['title']
        year = record['year'] if 'year' in record else None
        score = int(record['score'])
        imdb_id = record['imdb_id'] if 'imdb_id' in record else None
        criticker_id = record['criticker_id'] if 'criticker_id' in record else None
        filmweb_id = record['filmweb_id'] if 'filmweb_id' in record else None
        review = record['review'] if 'review' in record else None
        aka = None
        
        if 0 < score < 11:
            if criticker_id is not None:
                fetch_film_info_from_criticker(record)
                imdb_id = record['imdb_id']
                year = record['year']
                film_title = record['title']
                aka = record['aka']
    
            film = None
            if aka is not None:
                for title in aka:
                    logger.debug("try to search film %s by alternative title: %s (%s): %s" % (film_title, title, str(year), imdb_id))
                    film = search_film(film_title=title, year=year, imdb_id=imdb_id)
                    if film:
                        break
            else:
                logger.debug("try to search %s (%s): %s" % (film_title,
                                                            str(year), imdb_id))
                film = search_film(film_title=film_title, year=year,
                                   imdb_id=imdb_id)
    
            if film:
                logger.info("found movie %s: rated at %s" % (film, score))
                rate_film(film, film_title, year, score, review, overwrite)
            else:
                logger.debug("film %s not found" % film_title)
                if imdb_id:
                    logger.info("try to search by imdb_id: %s" % imdb_id)
                    movie = imdb_fetcher.get_movie_by_id(imdb_id, "http")
    
                    if movie:
                        film, status = imdb_fetcher.save_movie_to_db(movie)
                    else:
                        logger.error("Probably given IMDB_ID: %s is not a movie" %
                                     imdb_id)
    
                    if film:
                        if status == FilmToImport.ACCEPTED:
                            importedfilm = ImportedFilm(user=user, film=film)
                            importedfilm.save()
                            logger.info("imported movie %s" % film)
                        logger.info("found movie %s: rated at %s" % (film, score))
                        rate_film(film, film_title, year, score, review, overwrite)
                    else:
                        logger.error("Failed to import movie!. Continuing import anyway...")
    
                if not film:
                    logger.info("Film %s not rated" % film_title)
                    titles_not_rated.append(f(film_title, year))
        else:
            titles_not_rated.append(f(film_title, year))
        
    movies_not_rated = "; ".join(titles_not_rated)
    rating_import_log = ImportRatingsLog(user=user,
                                         movies_rated="; ".join(titles_rated),
                                         movies_already_rated="; ".join(titles_already_rated),
                                         movies_not_rated=movies_not_rated)
    rating_import_log.save()
    return movies_rated_list, movies_already_rated_list, movies_not_rated


class FilmwebError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class FilmwebRatingsFetcher(object):

    def __init__(self, user, filmweb_login, filmweb_password, kind, overwrite,
                 votes_url=None):
        logger.info("Create FilmwebRatingsFetcher")
        self.__create_browser_connection()
        self.__login_to_filmweb(filmweb_login, filmweb_password)
        if votes_url is None:
            self.fetch_user_name()
            self.fetch_user_id()
            votes_url = self.fetch_votes_history()

        self.create_ratings_array(votes_url)
        self.create_ratings_format()
        save_ratings_in_db(user, self.ratings, kind, overwrite)

    def __create_browser_connection(self):
        logger.info("Initialize mechanize.Browser")
        self.br = mechanize.Browser()

        logger.info("Create Cookie Jar")
        cj = cookielib.LWPCookieJar()
        self.br.set_cookiejar(cj)

        logger.info("Setup Browser options")
        self.br.set_handle_equiv(True)
        self.br.set_handle_gzip(False)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)
        self.br.set_debug_http(False)
        self.br.set_debug_responses(False)
        self.br.set_debug_redirects(False)

        # Follows refresh 0 but not hangs on refresh > 0
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        # User-Agent (this is cheating, ok?)
        self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686;en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    def __get_filmweb_cookie(self):
        logger.info("Get Filmweb Cookie")
        url = 'http://ssl.filmweb.pl/login'
        self.error_handling(url)

    def __login_to_filmweb(self, filmweb_login, filmweb_password):
        self.__get_filmweb_cookie()
        logger.info("Login to Filmweb")

        url = 'http://ssl.filmweb.pl/login'
        self.error_handling(url)
        # Select the second (index zero) form with username and password
        self.br.select_form(nr=1)

        # User credentials
        self.br.form['j_username'] = filmweb_login
        self.br.form['j_password'] = filmweb_password

        # Login
        self.br.submit()
        self.__is_user_logged_in()

    def __is_user_logged_in(self):
        url = 'http://ssl.filmweb.pl/login'
        html = self.error_handling(url)
        soup = BeautifulSoup(html)

        already_logged = soup.find("h2", {"class": "alreadyLogged"})
        if already_logged is None:
            raise FilmwebError(_("Cannot fetch ratings. Wrong username or password"))
            logger.error("Cannot log in user")
        else:
            logger.info("User is logged in")

    def fetch_user_name(self):
        url = 'http://filmweb.pl/'
        html = self.error_handling(url)
        soup = BeautifulSoup(html)

        filmweb_username = soup.find("a", {"class": "stdButton first"})
        if filmweb_username is None:
            raise FilmwebError(_("Cannot fetch username. Please try again later"))
        else:
            self.username = filmweb_username.contents[0].split()[0]
    
    def fetch_user_id(self):
        logger.debug("Fetch user_id for %s" % self.username)
        user_url = ("http://www.filmweb.pl/user/%s/films" % str(self.username))
        html = self.error_handling(user_url)
        soup = BeautifulSoup(html)

        user_id_pattern = re.compile('FilmwebSettings.widgets.userPublicProfile\["userId"\]="(\d+)"')
        user_public_profile = soup.find(text=user_id_pattern)
        if re.search(user_id_pattern, user_public_profile).groups()[0]:
            self.user_id = re.search(user_id_pattern,
                                    user_public_profile).groups()[0]
            logger.info("Filmweb user ID: %s" % (self.user_id))
        else:
            raise FilmwebError("Problem with fetching user ID for user %s" %
                         (self.username, ))

    def fetch_votes_history(self):
        logger.debug("Fetch film votes for user ID %s" % self.user_id)
        ratings_url = ('http://www.filmweb.pl/splitString/user/%s/filmVotes' %
                      str(self.user_id))
        html = self.error_handling(ratings_url)
        self.votes_url = html.read()
        return self.votes_url

    def create_ratings_array(self, votes_url=None):
        logger.debug("Create array from Filmweb history")
        votes_url = escape_text(votes_url)
        ratings_array = votes_url.split('\\a')
        if ratings_array is None:
            logger.error("Parsing error. Array with votes could not be constructed.")
            return []
        self.ratings_array = ratings_array[7:]
        return self.ratings_array

    def create_ratings_format(self):
        logger.debug("Parse the array with %s films" % len(self.ratings_array))

        """
        sample value for "film" variable
        \a[numer_filmu]\c[original title]\c[polish title (if empty,
        title is the same like original)]\c[rok]\c[favourite (0 - no; 1 - yes)]
        \c[rating]\c[poster url]\c[country code]\e[next country code (optional)
        \c[genre code]\e[next genre code (optional)\c[rating date: RRRRMMDD
        or nothing (if empty, that means that movie was rated before 20.10.2007)]
        """

        all_ratings = []
        for line in self.ratings_array:
            film_array = line.split('\c')
            filmweb_id = film_array[0]
            if film_array[1].endswith(", The"):
                filmname = "The " + film_array[1][:-len(", The")]
            elif film_array[1].endswith(", A"):
                filmname = "A " + film_array[1][:-len(", A")]
            else:
                filmname = film_array[1]
            localized_title = film_array[2]
            release_year = film_array[3]
            favorite = film_array[4]
            rating = film_array[5]
            img = film_array[6]
            review_date = film_array[9]

            all_ratings.append({"filmweb_id": filmweb_id, "title": filmname,
                                "year": release_year, "score": rating})
        self.ratings = all_ratings
        return all_ratings

    def error_handling(self, url):
        try:
            logger.info("Opening URL: %s" % url)
            html = self.br.open(url)
        except urllib2.HTTPError, e:
            logger.error("%d: %s" % (e.code, e.msg))
        except IOError, e:
            logger.error("%d: %s" % (e.code, e.msg))
        except:
            raise FilmwebError("Unexpected error %d: %s" % (e.code, e.msg))
        return html


def import_ratings():
    """
        Imports all ratings waiting to be imported in database
        Used in a cron job
    """
    ratings_to_import = ImportRatings.objects.filter(is_imported=False, attempts__lt=NUMBER_OF_ATTEMPTS).order_by('-submited_at')
    for rating_to_import in ratings_to_import:
        try:
            movies_list = json.loads(rating_to_import.movies)
            overwrite = rating_to_import.overwrite
            save_ratings(rating_to_import.user, movies_list, overwrite)

            rating_to_import.is_imported = True
            rating_to_import.imported_at = datetime.now()

        except Exception, e:
            logger.error( "Upps cannot import rating( %s ): %s" % ( rating_to_import, e ) )
            
            rating_to_import.import_status = ImportRatings.STATUS_IMPORT_FAILED
            rating_to_import.import_error_message = str( e )
            
        rating_to_import.attempts += 1
        rating_to_import.save()
        
        if rating_to_import.attempts == NUMBER_OF_ATTEMPTS and rating_to_import.import_status == ImportRatings.STATUS_IMPORT_FAILED:
            rating_to_import.send_import_failed_notification()
