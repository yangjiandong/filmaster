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
#!/usr/bin/env python
# encoding: utf-8 
import urllib
from xml.dom import minidom
from settings import *

yahoo_rankings_urls = {
        "thisweek":"http://rss.ent.yahoo.com/movies/thisweek.xml",
        "boxoffice":"http://rss.ent.yahoo.com/movies/upcoming.xml",
    }

yahoo_boxoffice_urls = {
        "boxoffice":"http://rss.ent.yahoo.com/movies/boxoffice.xml",
    }

moviecom_rankings = {
        "boxoffice":"http://www.movies.com/xml/rss/boxoffice.xml",
        "intheaters":"http://www.movies.com/xml/rss/intheaters.xml",
    }


def get_yahoo_movies_rankings(urls):
    raw_titles = []
    titles = []
    for url in urls:
        DOMTree = minidom.parse(urllib.urlopen(urls[url]))
        nodes = DOMTree.childNodes
        for i in nodes[1].getElementsByTagName("item"):
            raw_title= i.getElementsByTagName("title")[0].childNodes[0].toxml()
            raw_titles.append(raw_title)
        for raw_title in raw_titles:
            title, date = raw_title.split("opens")
            titles.append(title)
    return titles

def get_yahoo_boxoffice_rankings(urls):
    raw_titles = []
    titles = []
    for url in urls:
        DOMTree = minidom.parse(urllib.urlopen(urls[url]))
        nodes = DOMTree.childNodes
        for i in nodes[1].getElementsByTagName("item"):
            raw_title= i.getElementsByTagName("title")[0].childNodes[0].toxml()
            raw_titles.append(raw_title)
        for raw_title in raw_titles:
            title_money = raw_title.split(".")
           
            title = title_money[1][:-5]
            title = title[1:]
#            title, money = raw_title.split("-")
#            post, title = title.split(".")
            titles.append(title)
    return titles

def get_moviecom_rankings(urls):
    raw_titles = []
    titles = []
    for url in urls:
        DOMTree = minidom.parse(urllib.urlopen(urls[url]))
        nodes = DOMTree.childNodes
        for i in nodes[0].getElementsByTagName("item"):
            raw_title = i.getElementsByTagName("title")[0].childNodes[0].data
            raw_titles.append(raw_title)
        for raw_title in raw_titles:
            title = raw_title.split('-')
            titles.append(title[0])
        return titles

def save_titles(titles):
    file = open(MOVIE_LIST_FILE, 'w')
    for title in titles:
        file.write(title + '\n')
    file.close()

def main():            
    box_titles = get_yahoo_boxoffice_rankings(yahoo_boxoffice_urls)
    rankings_titles = get_yahoo_movies_rankings(yahoo_rankings_urls)
    moviecom_titles = get_moviecom_rankings(moviecom_rankings)
    titles = box_titles + rankings_titles + moviecom_titles
    save_titles(titles)

if __name__ == "__main__":
    main()
