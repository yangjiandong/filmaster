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
from settings import *
from BeautifulSoup import BeautifulSoup

urls = {
    "top250" : "http://www.imdb.com/chart/top",
    "action" : "http://www.imdb.com/chart/action",
    "adventure" : "http://www.imdb.com/chart/adventure",
    "biography" : "http://www.imdb.com/chart/biography",
    "comedy" : "http://www.imdb.com/chart/comedy",
    "crime" : "http://www.imdb.com/chart/crime",
    "documentary" : "http://www.imdb.com/chart/documentary",
    "drama" : "http://www.imdb.com/chart/drama",
    "family" : "http://www.imdb.com/chart/family",
    "fantasy" : "http://www.imdb.com/chart/fantasy",
    "filmnoir" : "http://www.imdb.com/chart/filmnoir",
    "history" : "http://www.imdb.com/chart/history",
    "horror" : "http://www.imdb.com/chart/horror",
    "independent" : "http://www.imdb.com/chart/independent",
    "music" : "http://www.imdb.com/chart/music",
    "musical" : "http://www.imdb.com/chart/musical",
    "mystery" : "http://www.imdb.com/chart/mystery",
    "romance" : "http://www.imdb.com/chart/romance",
    "scifi" : "http://www.imdb.com/chart/scifi",
    "short" : "http://www.imdb.com/chart/short",
    "sport" : "http://www.imdb.com/chart/sport",
    "thriller" : "http://www.imdb.com/chart/thriller",
    "war" : "http://www.imdb.com/chart/war",
    "western" : "http://www.imdb.com/chart/western",
#
    "1910s" : "http://www.imdb.com/chart/1910s",
    "1920s" : "http://www.imdb.com/chart/1920s",
    "1930s" : "http://www.imdb.com/chart/1930s",
    "1940s" : "http://www.imdb.com/chart/1940s",
    "1950s" : "http://www.imdb.com/chart/1950s",
    "1960s" : "http://www.imdb.com/chart/1960s",
    "1970s" : "http://www.imdb.com/chart/1970s",
    "1980s" : "http://www.imdb.com/chart/1980s",
    "1990s" : "http://www.imdb.com/chart/1990s",
    "2000s" : "http://www.imdb.com/chart/2000s",
}

def get_charts():
    file = open(IDS_LIST_FILE, 'w')
    for url in urls:
        #
        print "Zapisano: " + urls[url]
        site = urllib.urlopen(urls[url])
        #site = urllib.urlopen('/home/adam/Desktop/family.html')
        soup = BeautifulSoup(site)
        #print soup.originalEncoding

        tables = soup.findAll('table')
        
        for trs in tables[11]:
            tr = trs('a')
            for link in tr:
                aa = str(link.attrs[0][1])
                ww = aa.split('/title/tt')
                pt = ww[1].split("/")
                imdbid = str(pt[0])
                #title = unicode(lstr, "iso-8859-1")
                #title = unicode(aa,"utf-8")
                #backToBytes = title.encode( "utf-8" )

                #print backToBytes

                file.write(imdbid + '\n')
    file.close()
get_charts()


        

    
