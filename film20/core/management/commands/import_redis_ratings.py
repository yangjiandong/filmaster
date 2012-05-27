from film20.core.management.base import BaseCommand
from film20.core.models import Rating
from film20.core import rating_helper
from film20.utils import redis_intf

class Command(BaseCommand):
    def ratings(self):
        ratings = Rating.objects.all()
        ratings = ratings.filter(rating__isnull=False)
        ratings = ratings.values_list('user_id', 'rating', 'type', 'film_id', 'actor_id', 'director_id')
        return ratings

    def handle(self, *args, **kw):
        for n, (user_id, rating, type, film_id, actor_id, director_id) in enumerate(self.ratings()):
            redis_intf.rate(user_id, rating, film_id=film_id, actor_id=actor_id, director_id=director_id, type=type)
            if not (n % 1000):
                print n
