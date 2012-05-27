from django.core.management.base import BaseCommand
from django.db.models import Q

from optparse import make_option

import logging
from film20.import_films.tmdb_poster_fetcher import fetch_person_by_name, save_tmdb_poster
from film20.core.models import Person

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
    make_option('--all',
                  default=None,
                  dest = 'all',
                  action='store_true',
                  help='Fetch all posters for all persons - don\'t check tmdb_import_status'
      ),
      make_option('--name',
                  default=None,
                  dest = 'name',
                  action='store_true',
                  help='Fetch posters by person full name'
      ),
    )

    def handle(self, *args, **opts):
        self.opts = opts
        print opts
        persons = Person.objects.all()
        if not opts.get('all'):
            query = Q(tmdb_import_status=Person.NOT_IMPORTED) | \
                    Q(tmdb_import_status__isnull=True)
            persons = persons.filter(query)
        persons = persons.extra(select={'fieldsum': 'actor_popularity + director_popularity'},
                order_by=['-fieldsum',])

        tmdb_persos = None
        for person in persons:
            print "Looking for %s in tmdb" % person
            if opts.get('name'):
                try:
                    tmdb_person = fetch_person_by_name(person)
                except Exception, e:
                    print "Something went wrong for %s" % person
                    person.tmdb_import_status = Person.IMPORT_FAILED_OTHER_REASON
                    person.save()
                    print e
                    pass

            if tmdb_person:
                print "Found person with the same name and surname and birth year in tmdb"
                status = save_tmdb_poster(person, tmdb_person)
                if status:
                    print "Poster for %s saved" % person
                    person.tmdb_import_status = Person.IMPORTED
                    person.save()
                else:
                    person.tmdb_import_status = Person.IMPORT_FAILED_OTHER_REASON
                    person.save()
            else:
                person.tmdb_import_status = Person.IMPORT_FAILED_NO_OBJECT_IN_DB
                person.save()
                print "No entry in tmdb for person %s" % person
