import django.dispatch

film_rematched = django.dispatch.Signal( providing_args=["instance"] )
