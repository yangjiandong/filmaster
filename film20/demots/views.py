import json
from datetime import datetime

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from film20.demots.models import Demot
from film20.core.views import PaginatorListView
from film20.useractivity.models import UserActivity
from film20.demots.forms import AddDemotForm, AddDemotAjaxForm, AddBasedOnDemotForm

@login_required
def add_demot( request, template="demots/add.html" ):
    is_ajax = request.is_ajax()
    based_on = request.POST.get( "demot", False ) if request.method == "POST" else request.GET.get( "demot", False )
    if based_on is not False:
        based_on = get_object_or_404( Demot, pk=based_on )
    
    form_cls = AddBasedOnDemotForm if based_on else AddDemotForm
    if is_ajax:
        data = {}
        if not based_on:
            form_cls = AddDemotAjaxForm

    if request.method == "POST":
        form = form_cls( request.POST, request.FILES, user=request.user )
        
        if form.is_valid():
            demot = form.save( commit=False )
            demot.user = request.user
            demot.save()
            
            if is_ajax:
                data['success'] = True
                data['url'] = demot.get_absolute_url()
                data['demot_url'] = demot.final_image.url

            else:
                return redirect( demot.get_absolute_url()  )

        elif is_ajax:
            data['errors'] = dict([(k, [unicode(e) for e in v]) for k,v in form.errors.items()])

        if is_ajax:
            return HttpResponse( json.dumps( data ) )

    else:
        params = {}
        if based_on:
            params['based_on'] = based_on.pk
        form = form_cls( initial=params )
        if is_ajax:
            template = "demots/add-ajax.html"

    return render( request, template, {
        "form": form,
        "based_on": based_on,
        "demots": Demot.objects.all()[:3]
    })

@login_required
def remove_demot( request, pk ):
    demot = get_object_or_404( Demot, pk=pk, user=request.user )
    demot.delete()

    url = reverse( 'demots' )
    if request.is_ajax():
        return HttpResponse( url )

    return redirect( reverse( url ) )


class Demots( PaginatorListView ):
    template_name = "demots/list.html"
    context_object_name = 'activities'
    page_size = 20
    orders_map = {
        'created_at': { 'key': '-created_at', 'name': _( 'most recent' ), 'filters': {} },
        'popularity': { 'key': '-demot__like_counter__likes', 'name': _( 'most popular' ), 'filters': { 'featured': True } }
    }

    def get( self, *args, **kwargs ):
        self.order = self.request.GET.get( 'order', 'created_at' )
        if self.orders_map.has_key( self.order ):
            map = self.orders_map[ self.order ]
            self.order_by = map['key'] 
            self.filters = map['filters']
        else:
            self.order_by = 'created_at'
            self.filters = {}

        return super( Demots, self ).get( *args, **kwargs )

    def get_queryset( self ):
        return UserActivity.objects.filter( activity_type=UserActivity.TYPE_DEMOT, **self.filters ).order_by( self.order_by )

    def get_context_data( self, *args, **kwargs ):
        context = super( Demots, self ).get_context_data( *args, **kwargs )
        ctx = { 
            'order': self.order,
            'orders_map': self.orders_map
        }
        context.update( ctx )
        return context

demots = Demots.as_view();
