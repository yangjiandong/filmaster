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
from django.contrib import admin
from models import *

admin.site.register(Object, ObjectAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(PersonLog, PersonLogAdmin)
admin.site.register(Film, FilmAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(ObjectLocalized, ObjectLocalizedAdmin)
admin.site.register(FilmLocalized, FilmLocalizedAdmin)
admin.site.register(Character, CharacterAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(ShortReview, ShortReviewAdmin)
admin.site.register(ShortReviewOld, ShortReviewAdminOld)
admin.site.register(RatingComparator, RatingComparatorAdmin)
admin.site.register(Recommendation, RecommendationAdmin)
admin.site.register(FilmComparator, FilmComparatorAdmin)
admin.site.register(FilmLog, FilmLogAdmin)
admin.site.register(Poster, PosterAdmin)
admin.site.register(Trailer, TrailerAdmin)
