from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from film20.moderation.registry import registry
from film20.moderation.items import ModeratorTool
from film20.film_features.models import FilmFeature
from film20.film_features.views import EditFeaturesView

class ModerationEditFeaturesView( EditFeaturesView ):
    template_name = 'moderation/film_features/edit.html'
 
    def get_context_data( self, *args, **kwargs ):
        context = super( ModerationEditFeaturesView, self ).get_context_data( *args, **kwargs )
        moderated_items = registry.get_by_user( self.request.user )
        context.update({
            "all"            : self.request.method == 'GET' and self.request.GET.get( 'all', False ),
            "tag"            : self.request.method == 'GET' and self.request.GET.get( 'tag', '' ),
            "moderated_item" : registry.get_by_name( "film-features" ),
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools'],
            "from_moderation": True,
        })
        return context

class FilmFeaturesTool( ModeratorTool ):
    name = "film-features"
    permission = "core.can_edit_localized_title"
    verbose_name = _( "Film features" )

    def get_view( self, request ):
        all = request.method == 'GET' and request.GET.get( 'all', False )
        tag = request.method == 'GET' and request.GET.get( 'tag', '' )
        
        next_film_to_vote = FilmFeature.objects.next_film_to_vote( request.user, all_movies=all, tag=tag )
        if next_film_to_vote is None:
            return render( request, 'moderation/film_features/edit.html', { 'all': all, 'tag': tag } )
        return ModerationEditFeaturesView.as_view()( request, pk=next_film_to_vote.pk )

registry.register( FilmFeaturesTool() )
