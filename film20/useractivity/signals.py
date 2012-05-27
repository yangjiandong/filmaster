import django.dispatch

grouping_started = django.dispatch.Signal( providing_args=["instance"] )
grouping_finished = django.dispatch.Signal( providing_args=["instance"] )
