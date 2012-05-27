#!/usr/bin/env python

import os, sys, getopt
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings' 
#sys.path.append('c:/djcode/film20') 
from xml.dom import minidom
from film20.core.models import *


#XML_DATA_FILE = '../film20/test_data/michuk-allrankings.xml'
#NAME = 'michuk'
def import_rankings(NAME, XML_DATA_FILE):
    DOMTree = minidom.parse(XML_DATA_FILE)

    nodes = DOMTree.childNodes

    for i in nodes[0].getElementsByTagName("film"):
        film_title = i.getElementsByTagName("filmname")[0].childNodes[0].toxml()
        score = i.getElementsByTagName("score")[0].childNodes[0].toxml()
	score = int(score)
	# TODO: check if this if correct with proposed rating:
	#Ratings - mapping
        #1   0	0-9
	#1.5 1	10-19
	#2   2	20-29
	#2.5 3	30-39
	#3   4	40-49
	#3.5 5	50-59
	#4   6	60-69
	#4.5 7	70-79
	#5   8	80-89
	#5.5 9	90-99
	#6   10	100
	score /= 10
        films = Film.objects.filter(title = film_title)
        if films:
	    film = films[0]
            link = film.parent.permalink
            movies_rating = Rating.objects.filter(parent__permalink = link, user__username = NAME, type=Rating.TYPE_FILM)
            if movies_rating.count() == 0:
                user_name = User.objects.get(username = NAME)
                permalink = Object.objects.get(permalink = link, type=Object.TYPE_FILM)
                print permalink, score
                rating = Rating(user = user_name, parent = permalink, film = film, normalized = score, rating = score, type = Rating.TYPE_FILM )
                rating.save()


def main():
    options, arguments = getopt.getopt(sys.argv[1:],'u:f:')
    for option in options:
        print option
        if option[0] == "-u":
            NAME = option[1]
            print NAME
        elif option[0] == "-f":
            XML_DATA_FILE = option[1]
            print XML_DATA_FILE
            
    import_rankings(NAME, XML_DATA_FILE)
if __name__ == "__main__":
    main()
