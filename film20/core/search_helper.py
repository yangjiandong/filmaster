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
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django import forms 

from django.contrib.auth.models import User
from film20.core.models import Object
from film20.core.models import Film
from film20.core.models import Person
from film20.core.search_forms import *
from film20.utils.texts import *

import re
import logging
logger = logging.getLogger(__name__)

# TODO: Apply full-text search when we search blogs
# TODO: Disable search in case of stupid queries (one/two letter queries and so)     

class ExtraQ(Q):
  pass

EMPTY_SEARCH_RESULT = {        
    'best_results' : [],
    'results' : [],        
}

  
class SearchResult:
    def __init__(self, best_count=3, total_count=10):
        self.best = 3
        self.total = 10
        self.results = []
        
    def add_results(self, results):
        for r in results:
            if not r in self.results:
                self.results.append(r)
    
    def add_result(self, result):
        if not result in self.results:
            self.results.append(result)
    
    def count(self):
        return len(self.results)
        
    def result_dict(self):
        return { 'best_results' : self.results[:self.best], 'results' : self.results[self.best:self.total] }
  

class Search_Helper():
    
    # TODO: jakies cuda sie tu dzieja! zbadac!!!
    def exclude_previous_results(self, current_result, old_results):
        logger.debug("current_result=" + str(current_result))
        # for all old result lists
        for old_result in old_results:
            logger.debug("processing old_result=" + str(old_result))
            
            # TODO: czemu do cholery item in current_result nie pobiera wszystkich itemow z listy???
            # for all current results items
            for item in current_result:
                logger.debug("processing item=" + str(item))
                # if current item exists in the previous results, remove it
                if item in old_result:
                    logger.debug("Removing item from the list: " + unicode(item))
                    current_result.remove(item)
                # otherwise keep it
                else:
                    logger.debug("Keeping item: " + unicode(item))
        return current_result
        
    # TODO: somehow handle limit and offset
    def do_search(self, qlist, Type):
        """
        Generic helper for any searches. It goes through all the qsets in the qlist,
        executes the queries, excluding the results of the previous queries and finally 
        returns a dictionary with at most two values: best_results and results
        """
        results = [] 
        processed_queries = 0
        non_empty_resultsets = 0
        total_count = 0
        for q in qlist:
            if total_count > 10:
                logger.debug("Already have 10 or more results. Breaking the loop!")
                break

            if isinstance(q,ExtraQ) and total_count>0:
                continue

            logger.debug("Processing query:" + unicode(q))
            result = Type.objects.select_related().filter(q)
            logger.debug("Query result: " + str(result))
            count = result.count()            
            logger.debug("Query count:" + unicode(count))
            
            if count > 0:                
                result = result.distinct()
                if Type==Film:
                    result = result.order_by("-popularity")[:10]
                elif Type==Person:
                    result = result.order_by("-actor_popularity", "-director_popularity")[:10]
                result = self.exclude_previous_results(list(result), list(results))
                total_count = total_count + len(result)
                logger.debug("Total count:" + unicode(total_count))
                results.append(result)
                non_empty_resultsets += 1
            
            processed_queries += 1
            
        best_results = []
        other_results = []
        
        for current_results in results:
            if len(other_results)>6:
                break
            
            for item in current_results:
                logger.debug(item)
                if len(best_results)<3:
                    best_results.append(item)
                elif len(other_results)<7:
                    other_results.append(item)
                else:
                    break            
        return {
            'best_results' : best_results,
            'results' : other_results,
        }        

    def search_film_old(self, permalink=None, title=None, offset=0, limit=20):
        """
        Search films basing on the passed criteria
        TODO: use offset and limit
        """
                
        if permalink != None:               
            logger.debug("permalink != None")
            qlist = [ 
                # exact title
                ( Q(permalink__iexact=permalink) ),
                # title that starts with the search phrase
                ( Q(permalink__istartswith=permalink) ),
                # title containing the search phrase
                
                # TODO: rather remove this. It's a database killer -- cannot use
                # any indexes with such queries!!!
                ( Q(permalink__icontains=permalink) ),
            ]            
            return self.do_search(qlist, Film)            
                
        elif title != None:
            logger.debug("title != None")
            # trim the title
            title = title.lstrip() 
            title = title.rstrip() 
            # hack to show results with common prefixes as well
            thetitle = "The " + title
            leetitle = "Le " + title
            dertitle = "Der " + title
            dietitle = "Die " + title
            dastitle = "Das " + title
            qlist = [ 
                # exact title
                ( Q(title__iexact=title) ),
                ( Q(filmlocalized__title__iexact=title) ),
                # title that starts with the search phrase
                ( Q(title__istartswith=title) ),
                ( Q(filmlocalized__title__istartswith=title) ),
                
                # The title
                ( Q(title__istartswith=thetitle) ),
                ( Q(filmlocalized__title__istartswith=thetitle) ),
                
                # Le title
                ( Q(title__istartswith=leetitle) ),
                ( Q(filmlocalized__title__istartswith=leetitle) ),

                # Der/die/das title
                ( Q(title__istartswith=dertitle) ),
                ( Q(filmlocalized__title__istartswith=dertitle) ),
                ( Q(title__istartswith=dietitle) ),
                ( Q(filmlocalized__title__istartswith=dietitle) ),
                ( Q(title__istartswith=dastitle) ),
                ( Q(filmlocalized__title__istartswith=dastitle) ),

                # TODO: rather remove this. It's a database killer -- cannot use
                # any indexes with such queries!!!
                # title containing the search phrase
                ( ExtraQ(title__icontains=title) ),
                ( ExtraQ(filmlocalized__title__icontains=title) ),
            ]        
#            qlist = [ 
#                # exact title
#                ( Q(title__iexact=title) | Q(filmlocalized__title__iexact=title)),            
#                # title that starts with the search phrase
#                ( Q(title__istartswith=title) | Q(filmlocalized__title__istartswith=title)),
#                # title containing the search phrase
#                
#                # TODO: rather remove this. It's a database killer -- cannot use
#                # any indexes with such queries!!!
##                ( Q(title__icontains=title) | Q(filmlocalized__title__icontains=title) ),
#            ]          
            return self.do_search(qlist, Film)       
        else:
            logging.warn("Unexpected arguments!")
            # TODO: throw exception
            return EMPTY_SEARCH_RESULT
            
    def _execute_queries(self, qlist, best=3, limit=10):
        res = SearchResult(best_count=best, total_count=limit)
        for q in qlist:            
            for o in q[:limit*2]:
                res.add_result(o)
                if res.count()>=limit:
                    return res.result_dict()
        return res.result_dict()
            
    FILM_YEAR_RE = re.compile(r"(.*)\[(\d{4})\]$")
    
    def search_film(self, permalink=None, title='', offset=0, limit=10):
        #[turin] pagination doesn't work and there's no way of implementing it without considerable change in design.
        # Django 1.1 would help tremendously as it introduces aggregates (like max).
        # - how to paginate if result is returned from several queries, not one?
        # - fewer films are returned then rows actually fetched from the database in case we match against several keywords
        # I recomend we actually return SearchResult object and store needed data there.
        """
        Search films basing on the passed criteria
        TODO: use offset and limit
        """
    
        title = title and title.strip()
                
        if permalink != None:               
            logger.debug("permalink != None")
            query = Film.objects.distinct().select_related().order_by('-popularity')
            qlist = [ 
                # exact title
                query.filter(permalink__iexact=permalink),
                # title that starts with the search phrase
                query.filter(permalink__istartswith=permalink),
                # title containing the search phrase                
                # TODO: rather remove this. It's a database killer -- cannot use
                # any indexes with such queries!!!
                #TODO: do we do keywords on permalink? or what?
                query.filter(permalink__icontains=permalink),
            ]            
            return self._execute_queries(qlist, limit=limit)            
                
        elif title:
            logger.debug("title search")
            year = self.FILM_YEAR_RE.search(title)
            if year:
              title = year.group(1)
            # trim the title
            title = title.strip()             
            normalized = normalized_text(title)
            root = text_root_normalized(normalized)            
            letters = text_letters(normalized)
            query = Film.objects.distinct().select_related().order_by('-popularity')
            if year:
                query = query.filter(release_year = int(year.group(2)))
            qlist = [ 
                # search by film.title and filmlocalized.title
                # In my opinion, this is redundant and we could just do prefix search.
                query.filter(title__iexact=title),
                query.filter(filmlocalized__title__iexact=title),
                query.filter(title__istartswith=title),
                query.filter(filmlocalized__title__istartswith=title),
                #these two queries change only the precedence, showing titles starting 
                #with the search phrase earlier; they would be found during keyword search anyway.
				query.filter(title_normalized__startswith = normalized),
				query.filter(filmlocalized__title_normalized__startswith = normalized),
				#query.filter(title_root__startswith = root),
				#query.filter(filmlocalized__title_root__startswith = root),
                #favour shorter titles == closer matches
                query.filter(searchkey__key_normalized__startswith = normalized).order_by("searchkey__text_length"),
                query.filter(Q(searchkey__key_root__startswith = root)
                    | Q(searchkey__key_letters__startswith = letters)).order_by("searchkey__text_length")
            ]        
            return self._execute_queries(qlist, limit=limit)
            
        else:
            logging.warn("Unexpected arguments!")
            # TODO: throw exception
            return EMPTY_SEARCH_RESULT
            
    
    def search_person_by_name(self, person_name, person_surname):
        res = EMPTY_SEARCH_RESULT.copy()
           
        # This may only happen in advanced search
        if person_name!=None and person_surname==None:
            logger.debug("person_name!=None and person_surname==None")            
            qlist = [ 
                ( Q(name__iexact=person_name) ),
                ( Q(name__istartswith=person_name) ),
                ( Q(personlocalized__name__iexact=person_name) ),
                ( Q(personlocalized__name__istartswith=person_name) )
            ]                    
            # TODO: rather remove this. It's a database killer -- cannot use
            # any indexes with such queries!!!    
            # 'contains' search only if search phrase is long enough to make sense
#            if len(person_name)>3:
#                q_contains = Q(name__icontains=person_name)                
#                qlist.append(q_contains)
            res = self.do_search(qlist, Person)
            
        elif person_name==None and person_surname!=None:
            logger.debug("person_name==None and person_surname!=None")        
            qlist = [ 
                ( Q(surname__iexact=person_surname) ),
                ( Q(surname__istartswith=person_surname) ),                
                ( Q(personlocalized__surname__iexact=person_surname) ),
                ( Q(personlocalized__surname__istartswith=person_surname) )
            ]
            # TODO: rather remove this. It's a database killer -- cannot use
            # any indexes with such queries!!!            
            # 'contains' search only if search phrase is long enough to make sense
#            if len(person_surname)>3:
#                q_contains = Q(surname__icontains=person_surname)                
#                qlist.append(q_contains)
            res = self.do_search(qlist, Person)
            
        elif person_name!=None and person_surname!=None:
            logger.debug("person_name!=None and person_surname!=None")
            qlist = [
                # Exact results 
                ( Q(name__iexact=person_name) & Q(surname__iexact=person_surname) ),
                # One exact, the other starts with
                ( Q(name__istartswith=person_name) & Q(surname__iexact=person_surname) ),
                ( Q(name__iexact=person_name) & Q(surname__istartswith=person_surname) ),      
                # Both starts with
                ( Q(name__istartswith=person_name) & Q(surname__istartswith=person_surname) ),                
                ( Q(personlocalized__name__istartswith=person_name) & Q(personlocalized__surname__istartswith=person_surname))
            ] 
            # Either starts with
            q_either_startswith = ( 
                Q(name__istartswith=person_name) | Q(surname__istartswith=person_surname) 
            )
            # TODO: rather remove this. It's a database killer -- cannot use
            # any indexes with such queries!!!
            # Either contain            
#            q_either_contains = ( 
#                Q(name__icontains=person_name) | Q(surname__icontains=person_surname) 
#            )
            # additional search criteria if search phrase length is long enough
#            if len(person_name)>3 & len(person_surname)>3:                
#                qlist.append(q_either_startswith)
#                qlist.append(q_either_contains)                
                           
            res = self.do_search(qlist, Person)      
        else:
            logging.warn("Unexpected arguments!")
            # TODO: throw exception
        return res
    
    def search_person(self, permalink=None, person_name=None, person_surname=None, offset=0, limit=20):
        """
        Search people, basing on the params passed
        TODO: use offset and limit
        TODO: move '3' (minimum phrase length for some queries to config)
        """

        # trim stuff
        if person_name!=None:
            person_name = person_name.lstrip() 
            person_name = person_name.rstrip() 
        if person_surname!=None:
            person_surname = person_surname.lstrip() 
            person_surname = person_surname.rstrip() 

        if permalink != None:
            logger.debug("permalink != None")
            qlist = [ 
                ( Q(permalink__iexact=permalink) ),
                ( Q(permalink__istartswith=permalink) ),                
            ]            
            # 'contains' search only if search phrase is long enough to make sense
            if len(permalink)>3:
                q_contains = Q(permalink__icontains=permalink)            
                qlist.append(q_contains)
            return self.do_search(qlist, Person)                   
        
        res = self.search_person_by_name(person_name, person_surname)
            
        if not res['best_results'] and not res['results']:
            phrase = concatenate_words([person_name, person_surname])
            if len(phrase)>0:
                res = self.search_person_by_phrase(phrase, False)
        
        return res;
        
    def search_user(self, username=None, person_name=None, person_surname=None, offset=0, limit=20):
        """
        Search users, basing on the params passed.
        In case of advanced search, we're basing on the assumption that always either
        username or both person_name and person_surname are entered.
        TODO: use offset and limit
        """
        if username != None:
            # trim
            username = username.lstrip() 
            username = username.rstrip()
 
            logger.debug("username != None")
            qlist = [ 
                ( Q(username__iexact=username) ),
                ( Q(username__istartswith=username) ),
                # TODO: rather remove this. It's a database killer -- cannot use
                # any indexes with such queries!!!
#                ( Q(username__icontains=username) ),
            ]            
            return self.do_search(qlist, User)           
            
        # This may only happen in advanced search
        elif person_name!=None and person_surname==None:
            logger.debug("person_name!=None and person_surname==None")            
            qlist = [ 
                ( Q(first_name__iexact=person_name) ),
                ( Q(first_name__istartswith=person_name) ),
                # TODO: rather remove this. It's a database killer -- cannot use
                # any indexes with such queries!!!
 #               ( Q(first_name__icontains=person_name) ),
            ]            
            return self.do_search(qlist, User)
            
        elif person_name==None and person_surname!=None:
            logger.debug("person_name==None and person_surname!=None")        
            qlist = [ 
                ( Q(last_name__iexact=person_surname) ),
                ( Q(last_name__istartswith=person_surname) ),
                # TODO: rather remove this. It's a database killer -- cannot use
                # any indexes with such queries!!!
#                ( Q(last_name__icontains=person_surname) ),
            ]            
            return self.do_search(qlist, User)
            
        elif person_name!=None and person_surname!=None:
            logger.debug("person_name!=None and person_surname!=None")
            qlist = [
                # Exact results 
                ( Q(first_name__iexact=person_name) & Q(last_name__iexact=person_surname) ),
                # One exact, the other starts with
                ( Q(first_name__istartswith=person_name) & Q(last_name__iexact=person_surname) ),
                ( Q(first_name__iexact=person_name) & Q(last_name__istartswith=person_surname) ),      
                # Both starts with
                ( Q(first_name__istartswith=person_name) & Q(last_name__istartswith=person_surname) ),                
            ] 
            # Either starts with
            q_either_startswith = ( 
                Q(first_name__istartswith=person_name) | Q(last_name__istartswith=person_surname) 
            )
            # TODO: rather remove this. It's a database killer -- cannot use
            # any indexes with such queries!!!                
            # Either contain
#            q_either_contains = ( 
#                Q(first_name__icontains=person_name) | Q(last_name__icontains=person_surname) 
#            )

            # additional search criteria if search phrase length is long enough
#            if len(person_name)>3 & len(person_surname)>3:                
#                qlist.append(q_either_startswith)
#                qlist.append(q_either_contains)                
                           
            return self.do_search(qlist, User)      
        else:
            logging.warn("Unexpected arguments!")
            # TODO: throw exception
            return EMPTY_SEARCH_RESULT
                        
    def search_person_by_phrase(self, search_phrase, split=True):
        """
        Generic search with "People" option selected.
        """
        logger.debug("Szukamy osoby")
        search_phrase = search_phrase.strip()
        if not search_phrase:
            return EMPTY_SEARCH_RESULT
                
        if split:
            name_and_surname = self.split_into_name_and_surname(search_phrase)        
            search_results = self.search_person_by_name(name_and_surname['name'],  name_and_surname['surname'])
            if search_results['best_results']:
                return search_results
        
        normalized = normalized_text(search_phrase)
        root = text_root_normalized(normalized)            
        letters = text_letters(normalized)        
        
        query = Person.objects.distinct().select_related()
        qlist = [
            query.filter(searchkey__key_normalized__startswith = normalized).order_by("-actor_popularity", "-director_popularity", "searchkey__text_length"),                        
                query.filter(Q(searchkey__key_root__startswith = root)
                    | Q(searchkey__key_letters__startswith = letters)).order_by("-actor_popularity", "-director_popularity", "searchkey__text_length")                
        ]
        return self._execute_queries(qlist)
    
    def search_user_by_phrase(self, search_phrase):
        """
        Generic search with "User" option selected.
        """
        logger.debug("Szukamy osoby")

        search_phrase = search_phrase.strip()
        if not search_phrase:
            return EMPTY_SEARCH_RESULT
        name_and_surname = self.split_into_name_and_surname(search_phrase)        
        
        search_results1 = self.search_user(
            person_name = name_and_surname['name'], 
            person_surname = name_and_surname['surname']
        )
        
        search_results2 = self.search_user(
            username = search_phrase
        )
        
        logger.debug(search_results1)
        logger.debug(search_results2)        

        search_results = {
            "best_results" : list(search_results1['best_results']) + list(search_results2['best_results']),
            "results" : list(search_results1['results']) + list(search_results2['results']),
        }
        
        logger.debug(search_results)
        
        return search_results

    def search_film_person_by_phrase(self, search_phrase):
      search_results_film = self.search_film(title=search_phrase)
      search_results_person = self.search_person_by_phrase(search_phrase)
      search_results = {}
      search_results['best_results'] = list(search_results_film['best_results']) + list(search_results_person['best_results'])
      search_results['results'] = list(search_results_film['results']) + list(search_results_person['results'])
      return search_results
          
    def split_into_name_and_surname(self, search_phrase):
        """
        Splits the search phrase into name and surname by tokenizing it.
        We are taking the assumption that the last token is always the surname and any 
        previous ones merged together are names
        """
        search_phrase = search_phrase.strip()
        search_phrase_li = search_phrase.split(" ")
        logger.debug(search_phrase_li)
                        
        f_name = ""
        f_surname = ""
 
        if len( search_phrase_li ) == 0:
            # TODO: error?
            loggin.debug("No search phrase. Error?")
            None
        elif len( search_phrase_li ) == 1:
             f_name = None
             f_surname = search_phrase_li[0]     
        else:                   
            # create a name string                           
            for i in range( len( search_phrase_li )-1 ):
                current_word = search_phrase_li[i]
                # if looks like part of surname (Dd, Van, etc, append to surname)
                if self.looks_like_spart_of_surname(current_word):
                    f_surname += unicode(current_word) + " "
                else:
                    f_name += unicode(current_word)
                    if i != len( search_phrase_li )-2:
                        f_name += " "
            if f_name=='':
                f_name = None
            f_surname += search_phrase_li[len( search_phrase_li )-1]                     
        
        if f_name!=None:
            f_name = f_name.strip()
        if f_surname!=None:
            f_surname = f_surname.strip()
        
        logger.debug("name=["+unicode(f_name)+"]")
        logger.debug("surname=["+unicode(f_surname)+"]")
        return {
            "name" : f_name,
            "surname" : f_surname,
        }
    
    PREFIXES = {
        'ab':'ab',
        'Ab':'Ab',
        'abu':'abu',
        'Abu':'Abu',
        'bin':'bin',
        'Bin':'Bin',
        'bint':'bint',
        'Bint':'Bint',
        'da':'da',
        'Da':'Da',
        'de':'de',
        'De':'De',
        'degli':'degli',
        'Degli':'Degli',
        'della':'della',
        'Della':'Della',
        'der':'der',
        'Der':'Der',
        'di':'di',
        'Di':'Di',
        'del':'del',
        'Del':'Del',
        'dos':'dos',
        'Dos':'Dos',
        'du':'du',
        'Du':'Du',
        'el':'el',
        'El':'El',
        'fitz':'fitz',
        'Fitz':'Fitz',
        'haj':'haj',
        'Haj':'Haj',
        'hadj':'hadj',
        'Hadj':'Hadj',
        'hajj':'hajj',
        'ibn':'ibn',
        'Ibn':'Ibn',
        'ter':'ter',
        'Ter':'Ter',
        'tre':'tre',
        'Tre':'Tre',
        'van':'van',
        'Van':'Van',
        'Von':'Von',
        'von':'von',
    }

    
    def looks_like_spart_of_surname(self, word):
        if Search_Helper.PREFIXES.has_key(word):
            return True
        else:
            return False
