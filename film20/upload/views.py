import json, time

from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required

from .forms import UserUploadImageForm

@login_required
def upload_picture( request, template="upload/upload-image.html" ):
    return render( request, template )

@login_required
def upload_image( request ):

    data = {
        'success': False,
        'errors' : {
            '__all__': '#System error'
        },
    }

    if request.method == 'POST':
        form = UserUploadImageForm( request.POST, request.FILES )

        if form.is_valid():
            uploaded_image = form.save( commit=False )
            uploaded_image.uploaded_by = request.user

            uploaded_image.save()
            
            data['success'] = True
            data['image_id'] = uploaded_image.id
            data['image'] = uploaded_image.image.url

        else:
            data['errors'] = dict([(k, [unicode(e) for e in v]) for k,v in form.errors.items()])
    
    return HttpResponse( '<div id="response">%s</div>' % json.dumps( data ) )
