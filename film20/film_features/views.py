
from django import http
from django.conf import settings
from django.utils import simplejson as json
from django.views.generic import UpdateView, View

from film20.core.models import Film, SimilarFilm
from film20.film_features.forms import FilmFeaturesForm
from film20.film_features.models import TYPE_CHOICES, FilmFeature, FilmFeatureVote

SUGGEST_SIMILAR_FILMS = getattr( settings, 'SUGGEST_SIMILAR_FILMS', True )
NUMBER_OF_SUGGESTED_SIMILAR_FILMS = getattr( settings, 'NUMBER_OF_SUGGESTED_SIMILAR_FILMS', 5 )


class EditFeaturesView( UpdateView ):
    model = Film
    form_class = FilmFeaturesForm
    template_name = 'movies/movie/features/edit.html'

    def get_form_kwargs( self ):

        def suggested( o ):
            o.suggestion = True
            return o

        suggested_films = map( suggested, self.object.get_related_films()[:NUMBER_OF_SUGGESTED_SIMILAR_FILMS] ) if SUGGEST_SIMILAR_FILMS else []
        kwargs = { 
            'initial': { 
                'features': ','.join( [ str( v['type'] ) for v in FilmFeatureVote.objects.filter( user=self.request.user, film=self.object ).values( 'type' ) ] ),
                'similar_films': SimilarFilm.user_votes( film=self.object, user=self.request.user ) or suggested_films
            }
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_context_data( self, *args, **kwargs ):
        context = super( EditFeaturesView, self ).get_context_data( *args, **kwargs )
        context.update({
            'similar_films': SimilarFilm.get_similar( film=self.object ),
            'features'     : FilmFeature.objects.filter( film=self.object ),
            'voted'        : FilmFeature.objects.is_voted( self.object, self.request.user ),
            'preview'      : self.request.method == 'GET' and 'preview' in self.request.GET,
            'edit'         : self.request.method == 'GET' and 'edit' in self.request.GET,
        })
        return context

    def render_to_response( self, context ):
        if self.request.method == 'POST':
            return self.get_json_response( self.convert_context_to_json( context ) )
        return super( EditFeaturesView, self ).render_to_response( context )

    def get_json_response( self, content, **httpresponse_kwargs ):
        return http.HttpResponse( content,
                                  content_type='application/json',
                                  **httpresponse_kwargs )

    def convert_context_to_json( self, context ):
        return json.dumps( context )

    def form_valid( self, form ):
        features = form.cleaned_data['features'].split( ',' ) if form.cleaned_data['features'] else []
        similar_films = form.cleaned_data['similar_films']
        
        FilmFeatureVote.objects.filter( film=self.object, user=self.request.user ).delete()
        for t in features:
            FilmFeatureVote.objects.get_or_create( film=self.object, user=self.request.user, type=t )

        SimilarFilm.remove_vote( user=self.request.user, film_a=self.object )
        for sf in similar_films:
            SimilarFilm.add_vote( user=self.request.user, film_a=self.object, film_b=sf )

        return self.render_to_response({ 'success': True, 'features': features })
    
    def form_invalid( self, form ):
        result = {
            'success': False,
            'errors': dict([(k, [unicode(e) for e in v]) for k,v in form.errors.items()])
        }
        return self.render_to_response( result )

from film20.core.views import ajax_widget
from django.shortcuts import render_to_response, get_object_or_404
from film20.film_features.models import FilmFeatureComparisionVote
def compare_films( request, id=None ):
    if request.method == 'POST':
        cv = get_object_or_404( FilmFeatureComparisionVote, id=id, user=request.user )
        action = request.POST.get( 'action', None )
        if action in ( 'skip', 'eq', 'a', 'b' ):
            if action == 'skip':
                cv.status = FilmFeatureComparisionVote.STATUS_SKIPPED

            else:
                cv.status = FilmFeatureComparisionVote.STATUS_VOTED
                if action == 'a': cv.result = cv.film_a
                elif action == 'b': cv.result = cv.film_b

            cv.save()

        else: # TODO
            pass
        request.method = 'GET'
        request.GET = request.POST
    return ajax_widget( request, 'film_features', 'random_films_to_compare' )

edit = EditFeaturesView.as_view()
