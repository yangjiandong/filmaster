# encoding: utf-8 
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


import urllib
from settings import *
from BeautifulSoup import BeautifulSoup
from xml.dom import minidom
import re
def parse(movies_html, level):
    file = open(IDS_LIST_FILE, 'w')
    soup = BeautifulSoup(movies_html)
    divs = soup.findAll("div", attrs={"class" : "filmo"})

    for div in divs:
#        div = str(div)
#        firstLine = re.match('.*<a href="/title/tt(\d+)/">.*', div)
#        print firstLine.group(1).strip()
#        for line in div:
#            line = str(line)
#            line = line.replace("\n", "")
   
        for line in div:
            line = str(line)
            line = line.replace("\n", "")
            if re.match('<h5>.*</h5>*', line):
                pass
            elif re.match('<div>(.*)</div>', line):
                firstLine= re.match('<div>(.*)</div>', line) 
                votes = firstLine.group(1).strip()
                votes = votes.replace(",","")
                votes = int(votes)
 #               print votes
                if votes <= level:
                    break
#               else:
#                file.write(str(votes)+" ")
            elif re.match('(.*)<a href="/title/tt(\d+)/">.*', line):
                firstLine = re.match('(.*)<a href="/title/tt(\d+)/">.*', line)
                if firstLine != None:
                    imdbid = firstLine.group(2).strip()
                    print imdbid
                    file.write(imdbid + '\n')
    file.close()


if len(sys.argv) == 1:
    print "Usage %s <min number of votes> <imdb-vote-history-url>" % sys.argv[0]
    sys.exit(1)
level = int(sys.argv[1])
imdbUrl = sys.argv[2]
try:
    movies_html = urllib.urlopen(imdbUrl).read()
    parse(movies_html, level)
except IOError:
    print "Could not get %s" % imdbUrl
    sys.exit(2)
