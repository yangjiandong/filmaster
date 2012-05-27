from django.template import loader
from django.template import Context
from django.http import HttpResponse
from film20.config.urls import templates
from django.views.decorators.cache import cache_page

from film20.import_films.models import ImportedFilm
from film20.import_films.models import FilmToImport

@cache_page(60 * 5)
def import_film_rss(request):
    imported = ImportedFilm.objects.all().order_by("-created_at")[:20]
    response = HttpResponse(mimetype='application/rss+xml')
    t = loader.get_template(templates['IMPORT_FILMS_RSS'])
    c = Context({'imported': imported,})
    response.write(t.render(c))
    return response
