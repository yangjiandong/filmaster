from django import template
from film20.upload.forms import UserUploadImageForm

register = template.Library()

@register.inclusion_tag( 'upload/upload-image-form.html' )
def upload_image_form( id ):
    return {
        'form': UserUploadImageForm(),
        'id'  : id
    }
