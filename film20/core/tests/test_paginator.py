from film20.utils.test import TestCase
from django.test.client import RequestFactory

from film20.core.views import PaginatorListView
from film20.core.models import Person

class InfListView(PaginatorListView):
    page_size = 5
    model = Person

class PaginatorTestCase(TestCase):
    fixtures = ['test_films.json']

    def test_inf_paginator(self):
        view = InfListView.as_view()
       
        with self.assertNumQueries(1):
            request = RequestFactory().get('/')
            response = view(request)
            items = list(response.context_data['object_list'])
            self.assertEquals(len(items), 5)

        # iterate through all pages
        items = []
        page = 1
        while True:
            response = view(RequestFactory().get('/?page=%d' % page))
            items.extend(response.context_data['object_list'])
            if not response.context_data['page_obj'].has_next():
                break
            page += 1

        self.assertEquals(len(items), Person.objects.count())

