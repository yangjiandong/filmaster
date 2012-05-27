from film20.utils.template import Library
from film20.film_features.models import FilmFeatureComparisionVote
register = Library()

@register.widget( 'movies/movie/features/compare_random_films.html' )
def random_films_to_compare( request ):
    user = request.user
    return {
       'to_vote': FilmFeatureComparisionVote.objects.next_to_vote( user ) if user.is_authenticated() else None
    }
