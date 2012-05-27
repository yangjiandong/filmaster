#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski, Osama Khalid).
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
#!/usr/bin/python

# (C) 2009 Lukasz Bolikowski

import re, urllib
from types import UnicodeType
import codecs
from xml.dom import minidom
from film20.utils.texts import deogonkify
from film20.import_films import tmdb

import logging
logger = logging.getLogger(__name__)

class SynopsisFetcher:
   def get_movie_urls(self, title, year = None):
      """Returns a list of search results for a given query.  Each result is a hash with keys: 'url', 'title' and 'year'."""
      pass
   def get_movie_synopses(self, url):
      """Returns a list of synopses for a given movie.  Each synopsis is a hash with keys: 'synopsis', 'url', 'author' and 'distributor'."""
      pass

class FdbSynopsisFetcher(SynopsisFetcher):
   def get_movie_urls(self, title, year = None):
      try:
         title = deogonkify(title) 
         s = "Fetching: " + title
         logger.info(s)
         query_url = 'http://fdb.pl/szukaj?query=' + urllib.quote_plus(title)
         contents = urllib.urlopen(query_url).read()
         results = []
         for line in contents.split('\n'):
            line_match = re.match('^\s*<a href="http://fdb.pl/film/(\d+-[^"]+)">(.*) \((\d{4}(?:/I+)?)\)</a>\s*$', line)
            if not line_match:
               continue
            result_url = 'http://fdb.pl/film/' + line_match.group(1).strip()
            result_title = line_match.group(2).strip()
            result_year = line_match.group(3).strip()
            if (year == None) or (str(year)[0:4] == result_year[0:4]):
               results += [{'url': result_url, 'title': result_title, 'year': result_year}]
         return results
      except Exception, e:
         logger.exception(e)

   def get_movie_synopses(self, url):
      try:
         contents = urllib.urlopen(url + '/opisy').read()
         synopses = []
         ignore = True
         synopsis = None
         for line in contents.split('\n'):
            if ignore:
               if re.match('^\s*<h2 class="category-header">Opisy filmu</h2>\s*$', line):
                  ignore = False
               else:
                  continue
            if synopsis == None:
               if re.match('^.*<p>\s*$', line):
                  synopsis = []
            elif re.match('^\s*</p>\s*$', line):
               author = synopsis[-1].strip()
               distributor = (author == '(opis dystrybutora)')
               synopsis = ' '.join(synopsis[:-2]).strip()
               synopses += [{'synopsis': synopsis, 'url': url, 'author': author, 'distributor': distributor}]
               synopsis = None
            else:
               synopsis += [line]

            if re.match('^\s*<div class="clear"></div>\s*$', line):
               break
         return synopses
      except IOError, e:
          logger.exception(e)
        
class FilmwebSynopsisFetcher(SynopsisFetcher):
   def get_movie_urls(self, title, year = None):
      try:
         title = deogonkify(title) 
         query_url = 'http://www.filmweb.pl/szukaj?c=film&q=' + urllib.quote_plus(title)
         contents = urllib.urlopen(query_url).read()
         results = []
         continued = False
         for line in contents.split('\n'):
            if continued:
               continued = False
               line_match = re.match('^\s*\((\d{4})\).*$', line)            
               if not line_match:
                   continue
               result_year = line_match.group(1).strip()
               if (year == None) or (str(year)[0:4] == result_year[0:4]):
                  results += [{'url': result_url, 'title': result_title, 'year': result_year}]
            line_match = re.match('^\s*<a class="searchResultTitle" href="([^"]+)">(.*)</a>\s*$', line)
            if not line_match:
               continue
            result_url = line_match.group(1).strip()
            result_title = line_match.group(2).strip()
            continued = True
         return results
      except Exception, e:
          logger.exception(e)

   def get_movie_synopses(self, url):
      try:
         contents = urllib.urlopen(url).read()
         final_url = None
         for line in contents.split('\n'):
             line_match = re.match('^\s*<li><a title="[^"]*" href="([^"]*)">opisy</a>.*$', line)
             if line_match:
                 final_url = line_match.group(1)
                 break
         if not final_url:
            return []
         contents = urllib.urlopen(final_url).read()
         synopses = []
         synopsis_next = False
         for line in contents.split('\n'):
            if synopsis_next:
               synopsis_next = False
               author = ''
               synopsis = line.strip()
               synopsis = re.sub(r'<a[^>]*>([^<]*)</a>', r'\1', synopsis)
               distributor = False
               synopses += [{'synopsis': synopsis, 'url': url, 'author': author, 'distributor': distributor}]
            if re.match('^\s*<li><p style="text-align:justify">\s*$', line):
               synopsis_next = True
         return synopses
      except IOError:
         # TODO: exception handling
         raise IOError
     
class RottenTomatoesSynopsisFetcher(SynopsisFetcher):
   def get_movie_urls(self, title, year = None):    
      title = deogonkify(title) 
      s = "Fetching: " + title
      logger.info(s)
      query_url = "http://uk.rottentomatoes.com/search/full_search.php?search=" + urllib.quote_plus(title)
      try:
         # windows-1252
         contents = (codecs.getreader("windows-1252")(urllib.urlopen(query_url))).read()

         results = []
         continued = False
         for line in contents.split('\n'):
            if continued:
               line_match = re.match('^\s*<td class="lastCol date" width="15%"><p><strong>(\d{4})<\/strong><\/p><\/td>.*$', line)
               if not line_match:
                   continue               
                   
               result_year = line_match.group(1).strip()

               # only record the result if the year matches (or is null)
               if (year == None) or (str(year)[0:4] == result_year[0:4]):
                  results += [{'url': result_url, 'title': result_title, 'year': result_year}]
               else:
                   continued = False
            else:      
                line_match = re.match('^\s*<a href="/m/([^"]+)">(.+)</a>\s*$', line)
                if not line_match:
                   continue
                result_url = "http://rottentomatoes.com/m/"+line_match.group(1).strip()
                #            result_title = line_match.group(2).strip()
                result_title = title
                continued = True
         return results
      except UnicodeDecodeError, e:
          logger.exception(e)
          return None
      except IOError:
          raise IOError

   def get_movie_synopses(self, url):
      try:
         contents = (codecs.getreader("windows-1252")(urllib.urlopen(url))).read()
         synopses = []
         synopsis = None
         synopsis_next = False
         # indicates that we found the synopsis
         continued = False 
         # indicates that we're processing the synopsis line by line now
         inside_synopsis = False 
         
         for line in contents.split('\n'):
            if continued:
               # check for whole synopsis in one line
               line_match = re.match('^\s*<span id="movie_synopsis_all" style="display: none;">(.+)</span>.*$', line)
               if not line_match:
                   # check for start of synopsis (to append lines later on)
                   line_match_start = re.match('^\s*<span id="movie_synopsis_all" style="display: none;">(.+).*$', line)
                   line_match_end = re.match('^\s*(.+)</span>.*$', line)
                   if line_match_start!=None:
                       synopsis = line_match_start.group(1).strip()
                       inside_synopsis = True
                       continue
                   elif (line_match_end!=None) & inside_synopsis:
                       # check for end of synopsis
                       synopsis += line_match_end.group(1).strip()
                       # end synopsis processing
                       continued = False
                   elif inside_synopsis:
                       # otherwise, we're inside synopsis, so just append current line
                       synopsis += line 
                       inside_synopsis = True
                       # TODO: set max number of lines to make sure we don't end up including whole HTML 
                       # in synopsis if something goes wrong
                   else:
                        # not found synopsis yet, keep looking
                        continue
               else:
                   synopsis = line_match.group(1).strip()
                   continued = False
               
            line_match = re.match('^\s*<span class="label">Synopsis:</span>\s*$', line)
            if not line_match:
               continue
            continued = True
         if (synopsis != None):
             synopses += [{'synopsis': synopsis, 'url': url, 'author': 'RottenTomatoes', 'distributor': False}]
                  
         return synopses
      except UnicodeError,e:
          logger.exception(e)
          return []
      except IOError:
         raise IOError

class TmdbSynopsisFetcher(SynopsisFetcher):
    def get_movie_urls(self, title, year=None):
        """
            Returns tmdb movie instance instead of url to movie
        """
        try:
            s = "Fetching: " + title
            results = tmdb.search(title)
            for result in results:
                logger.debug('Trying to fetch synopsis for: %s' % title )
                film_to_fetch = result
                prod_date = film_to_fetch['released']
                if prod_date:
                    production_year, month, day = prod_date.split("-")
                    if year == int(production_year):
                        tmdb_film = tmdb.getMovieInfo(film_to_fetch['id'])
                        logger.debug('Found in tmdb: %s' % tmdb_film["name"])
                        return [{'url': tmdb_film }]
        except Exception, e:
            logger.exception(e)
            
    def get_movie_synopses(self, url):
        try:
            synopses = []
            synopsis = url["overview"]
            title = unicode(url["name"])
            if synopsis == "No overview found." or synopsis == "" or synopsis == " ":
                synopsis = None
            if synopsis is not None:
                synopsis = synopsis.lstrip("\"").rstrip("\"")
                url = url["url"]
                synopses += [{'synopsis': synopsis, 'url': url, 'author': 'TMDb', 'distributor': False, 'title':title }]
                return synopses
        except Exception, e:
            logger.exception(e)


def get_synopses(title, year = None, fetcher_type="fdb"):

    if fetcher_type=="fdb":
        fetcher = FdbSynopsisFetcher()
    elif fetcher_type=="filmweb":
        fetcher = FilmwebSynopsisFetcher()
    elif (fetcher_type=="rottentomatoes") | (fetcher_type=="rt"):
        fetcher = RottenTomatoesSynopsisFetcher()
    elif fetcher_type=="tmdb":
        fetcher = TmdbSynopsisFetcher()
    elif (fetcher_type=="enwikipedia") | (fetcher_type=="enwp"):
        fetcher = WikipediaFetcher()

        # Because Wikipedia is handled by its nice API, it needs a special method.
        #fetcher = EnglishWikipediaSynopsisFetcher()
        #for article_title in fetcher.get_movie_title(title, year):
        #  # Return the synopsis.
        #  return fetcher.get_movie_synopses(title)
        #else: # If no items are there, return.
        #  return None
    else:
        logger.error("Unknown fetcher type: " + fetcher_type + ". Exiting!")
        return
    
    urls = fetcher.get_movie_urls(title, year)
    if urls == None:
        return None
    elif len(urls) == 0:
        return None
        
    synopses = fetcher.get_movie_synopses(urls[0]['url'])

    if synopses is None:
        return None

    if len(synopses) == 0:
        return None
    return synopses

class EnglishWikipediaSynopsisFetcher(SynopsisFetcher):
  # Written originally by Osama Khalid.
  def __init__(self):
    self.wikipedia_article = ""

  def isItFilmArticle(self, title):
    """Wikipedia film articles have things in common. This method tries to check whether this article has them"""
    filmYearCategory = re.compile('Category:(.*?)\d{4} film(.*?)')
    filmInfobox = re.compile('\{\{( *)(Infobox (film|movie)|Film infobox)', re.IGNORECASE)

    xmlString = urllib.urlopen('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=%s' % urllib.quote(unicode(title).encode('utf-8'))).read()
    xmlObject = minidom.parseString(xmlString)
    self.wikipedia_article = xmlObject.getElementsByTagName('rev')[0].childNodes[0].data

    # Check if it has a film infobox (like most Wikipedia's film articles).
    if filmInfobox.search(self.wikipedia_article) is not None:
      return True
    # Check if it has a film-by-year category (such as Cageory:2009 films).
    elif filmYearCategory.search(self.wikipedia_article) is not None:
      return True

  def get_movie_title(self, film_title, year=""):
    """Uses Wikipedia search API to get the film artilce titles."""

    # if the year isn't given in the first place, make it empty string (instead of 'None').
    if year is None: year = ""

    try:
        s = "Searching for \'%s %s film\' in Wikipedia." % (film_title, year)
        logger.info(s)
    except Exception, e:
        # Added catching exceptions as sometimes unicode errors are thrown here
        # As described in: http://jira.filmaster.org/browse/FLM-405
        # Proper fix would be nice here
        logger.exception(e)
 
    # Search for '{{film_title}} {{year}} film' (i.e. 'Ice Age 2002 film')
    xmlString = urllib.urlopen('http://en.wikipedia.org/w/api.php?action=query&list=search&format=xml&srsearch=' + urllib.quote(unicode(film_title).encode('utf-8') + ' ' + str(year)  + ' film')).read()

  
    xmlObject = minidom.parseString(xmlString)
    
    try: 
        # Get 10 first results (by default, the API gives 10 results. I think it's enough). 
        for result in xmlObject.getElementsByTagName('p'):
          title = result.getAttributeNode('title').value
          if self.isItFilmArticle(title):
            # return Wikipedia article title.
            return [title]
          else:
            s =  "\'%s\' doesn't seem like a film article. Skipping." % title
            logger.info(s)
    # Probably to be fixed in http://jira.filmaster.org/browse/FLM-205
    except Exception, e:
        logger.exception(e)

    logger.info("No results from Wikipedia.")
    return []
  
  def get_movie_synopses(self, article_title):
    """Gets the whole wikipedia article, extracts the fist paragrpah in 'Plot' section, removes any wiki markups and returns the output."""

    # Find first paragraph (first non-template non-comment line) after "Plot", "Summery" or "Synopsis" sections.
    splitPlot = re.compile(r'==( *)(Plot|Summery|Synopsis|Plot summary)( *)==(\n)+(<!--.*?-->\n)*(\[\[(Image|File):(.*?)\]\](\n)*)*(\{\{.*?\}\}\n)*(\n)*(?P<plot>[^=\n]*)', re.IGNORECASE) 
    # Find internal links ([[Sid]] or [[Sid (Ice Age)|Sid]])
    intenalLinks = re.compile(r'\[\[(.*?)(\|)?([^\|]*?)\]\]')
    # Find external links ([http://filmaster.com Filmaster] or [http://filmaster.com]
    externalLinks = re.compile(r'\[(.*?)( (.*?))?\]')
    #Find Templates ({{text}})
    templates = re.compile(r'\{\{(.*?)\}\}')
  
    try:
      originalText = splitPlot.search(self.wikipedia_article).group('plot') # Get first paragraph
    except AttributeError:
      logger.debug("No plot found.")
      return None 
  
    changedText = intenalLinks.sub(r'\3', originalText) # Remove internal links
    changedText = externalLinks.sub(r'\1', changedText) # Remove external links
    changedText = templates.sub('', changedText)        # Remove templates
    changedText = changedText.replace('\'\'\'', '')     # Remove bold text markup ('''text''')
    changedText = changedText.replace('\'\'', '')       # Remove italic text markup (''text'')
  
#    print changedText # Only for debugging. Remove it after testing.
  
    # Return the synopsis.
    return [{'synopsis': changedText, 'url': 'http://en.wikipedia.org/wiki/' + urllib.quote(unicode(article_title).encode('utf-8')), 'author': 'Wikipedia', 'distributor': False}]


from .wikipedia import Wikipedia
class WikipediaFetcher( Wikipedia, SynopsisFetcher ):

    def __init__( self ):
        self.__obj = None

    def __get_obj( self, title, year=None ):
        if not self.__obj:
            wiki = Wikipedia()
            self.__obj = self.search_film( title, year )
        return self.__obj

    def get_movie_urls( self, title, year = None ):
        obj = self.__get_obj( title, year )
        if obj:
            return [{ 'url': obj }]

    def get_movie_synopses( self, obj ):
        if obj:
            synopsis = self.cut_synopsis( obj['text'] )
            return [{ 'synopsis': synopsis, 
                      'url': obj['url'], 
                      'author': 'Wikipedia', 
                      'distributor': False }]

#print get_synopses('Crash', 2004)
