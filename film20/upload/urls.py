from django.conf.urls.defaults import patterns, url

urlpatterns = patterns( 'film20.upload.views',
    url( r'^upload/image/$', 'upload_image', name='upload-image' ),
    url( r'^upload/picture/$', 'upload_picture', name='upload-picture' ),
)

