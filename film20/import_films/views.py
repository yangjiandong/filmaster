# Create your views here.
import re
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.paginator import Paginator
from django.core.paginator import InvalidPage
from django.core.paginator import EmptyPage
from django.utils.translation import ugettext as _
from django.contrib import messages

from film20.config.urls import templates
from film20.import_films.models import ImportedFilm, FilmToImport
from film20.import_films.forms import FilmToImportForm

NUMBER_OF_FILMS = 20

def import_film(request):
    imported_films = ImportedFilm.objects.all().order_by("-created_at")
    

    if request.user.is_authenticated() & (request.method == 'POST'):
        form = FilmToImportForm(request.user, request.POST)
        if form.is_valid():
            film_to_import = form.save(commit=False)
            film_to_import.user = request.user
            if form.cleaned_data['imdb_url']:
                url = form.cleaned_data['imdb_url']
                line = re.search('/tt(\d+)/', url)
                if line <> None:
                    film_to_import.imdb_id = line.group(1).strip()
            film_to_import.save()
            form = FilmToImportForm()

            # if user has perm to accept film, do this now
            if request.user.has_perm( 'import_films.can_accept_films' ):
                film_to_import.accept( request.user )
                message = _( "Film added to import!" )

            else:
                message = _("Thank you for this suggestion!")

            messages.add_message(request, messages.INFO, message )
            data = {
                'imported_films' : imported_films,
                'form' : form,
                }
            return render_to_response(templates['ADD_FILM'], data, context_instance=RequestContext(request))            
    else:
        imdb_id=request.GET.get('imdb_id','')
        imdb_url = 'http://www.imdb.com/title/tt'+request.GET.get('imdb_id','')+'/' if imdb_id else ''
        title = request.GET.get('title')
        form = FilmToImportForm(instance=FilmToImport(imdb_id=imdb_id, imdb_url=imdb_url, title=title))
    
    data = {
        'imported_films' : imported_films,
        'form' : form,
        }
    
    return render_to_response(templates['ADD_FILM'], data, context_instance=RequestContext(request))

def import_film_admin(request):
    films_to_import = FilmToImport.objects.filter(status=FilmToImport.UNKNOW)
    if request.method == "POST":
        if "accepted" in request.POST:
            log_id = int(request.POST.get('film_to_import_id'))
            log = FilmToImport.objects.get(id=log_id)
            log.status = FilmToImport.ACCEPTED
            log.save()
        if "not_accepted" in request.POST:
            log_id = int(request.POST.get('film_to_import_id'))
            log = FilmToImport.objects.get(id=log_id)
            log.status = FilmToImport.NOT_ACCEPTED
            log.save()
    print films_to_import
    data = {
        'films_to_import':films_to_import,
    }
    
    return render_to_response(templates['IMPORT_FILMS_ADMIN'], data, context_instance=RequestContext(request))
