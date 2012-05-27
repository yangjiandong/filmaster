import django.dispatch

post_commit = django.dispatch.Signal( providing_args=["instance"] )
