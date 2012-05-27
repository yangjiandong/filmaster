#!/usr/bin/env python
import os, getopt, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from django.utils.translation import gettext as _
_("foo")
from film20.import_films.imdb_fetcher import run

def main():
    
    options, arguments = getopt.getopt(sys.argv[1:],'pulifm:')

    opts = dict(options)

#    if "-c" not in opts:
#        raise getopt.GetoptError("Podaj rodzaj polaczenia \"sql\" dla lokalnej bazy, lub \"http\" dla bazy imdb.com")
    if "-p" in opts and "-u" in opts:
        raise getopt.GetoptError("Nie mozna uzyc opcji -p i -u na raz!")
    if "-l" in opts and "-m" in opts:
        raise getopt.GetoptError("Nie mozna uzyc opcji -l i -m na raz!")
   
    pickle = "-p" in opts
    unpickle = "-u" in opts
    list = "-l" in opts

    single_movie =  "-m" in opts
    single_movie_title = opts.get('-m','').replace('"',"")

    idlist =  "-i" in opts
    cron_job = "-f" in opts
        
#    if "-c" in opts:
#        conntype = opts['-c'].replace('"',"")
#    else:
#        raise getopt.GetoptError("Podaj rodzaj polaczenia -c \"sql\" dla lokalnej bazy, lub -c \"http\" dla bazy imdb.com")
    conntype = "http"
    run(pickle, unpickle, list, single_movie, idlist, cron_job, conntype, single_movie_title)

if __name__ == "__main__":
    main()
