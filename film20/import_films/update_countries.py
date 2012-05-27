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
import os, re

from django.conf import settings

from film20.core.models import Film, Country
from imdb_fetcher import save_country_list

countries = [ i.strip() for i in open( os.path.join( os.path.dirname(__file__), "countries.list" ) ) ]
pattern = re.compile( "|".join( countries ) )


def update_film( film ):
	final_countries = []
	country_list = film.production_country_list
	if country_list:
		for country in country_list.split( "," ):
			if country in countries:
				final_countries.append( country )
			else:
				try:
					Country.objects.get( country=country ).delete()
				except Country.DoesNotExist:
					pass

				for c in pattern.findall( country ):
					final_countries.append( c )
		
		film.production_country.clear()
		save_country_list( film, final_countries )

def update_films( qs ):
	for f in qs:
		update_film( f )

def update_all_films():
	update_films( Film.objects.all() )

if __name__ == "__main__":
	update_all_films()
