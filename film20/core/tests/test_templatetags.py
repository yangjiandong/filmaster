#-*- coding: utf-8 -*-
import os
import unittest
try:
    from PIL import Image
except:
    import Image

from django.core.files import File
from django.contrib.flatpages.models import FlatPage
from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT

from film20.core.models import Film
from film20.core.templatetags.sanitize import sanitize
from film20.core.templatetags.truncatechars import truncatechars
from film20.core.templatetags.format_date import human_readable_date
from film20.core.templatetags.filmaster_recommends import filmaster_recommends
from film20.utils.posters import get_image_path
from film20.utils.test import TestCase

class TemplatetagsTestCase(TestCase):

    def initialize(self):
        self.clean_data()

        # set up film
        self.film = Film()
        self.film.title = "Battlefield Earth II"
        self.film.type = Film.TYPE_FILM
        self.film.permalink = "battlefirld-earth-ii"
        self.film.release_year = 2010
        self.film.save()
        filename = "First_blood_poster.jpg"
        myfile = MEDIA_ROOT + "test/First_blood_poster.jpg"
        f = open(myfile, 'rb')
        myfile = File(f)
        self.film.image.save(filename, myfile)

    def clean_data(self):
        Film.objects.all().delete()
    
    def test_sanitize(self):

        text_before = u"<żarcik>To wcale nie jest śmieszne!!</żarcik>"
        allowed_tags = "b i em strong ol li ul blockquote a:href img:src h2 spoiler"

        text_after = sanitize(text_before, allowed_tags)

        self.failUnlessEqual(text_after, u"<&#380;arcik>To wcale nie jest &#347;mieszne!!")

        text_before = u"<h1>Lorem ipsum</h1>"
        text_after = sanitize(text_before, allowed_tags)

        self.failUnlessEqual(text_after, u"Lorem ipsum")

    def test_truncatechars(self):

        text_before = "Lorem ipsum"
        text_after = truncatechars(text_before, 4)
        self.failUnlessEqual(text_after, "Lorem")

        text_before = "Lorem ipsum sial la la"
        text_after = truncatechars(text_before, 5)
        self.failUnlessEqual(text_after, "Lorem")
        
        text_before = "Lorem ipsum sial la la"
        text_after = truncatechars(text_before, 6)
        self.failUnlessEqual(text_after, "Lorem ipsum")

    def test_allowed_tags(self):
        """
            ALLOWED TAGS set h5, img with src attribute
        """
        text_before = u"Lorem <h3>ipsum</h3> <h1>lorem</h1> <h5>ipsum</h5> <img src=\"#\" />"
        allowed_tags = "h5 img:src"

        text_after = sanitize(text_before, allowed_tags)
        self.failUnlessEqual(text_after, u"Lorem ipsum lorem <h5>ipsum</h5> <img src=\"#\" />")

    def test_poster(self):

        self.initialize()

        thumb_img = get_image_path(self.film, 80, 40)

        thumb_img = thumb_img[7:]

        cc =  MEDIA_ROOT + thumb_img
        img = Image.open(cc)
        size = img.size
        
        # x size
        self.failUnlessEqual(size[0], 80)

        # y size
        self.failUnlessEqual(size[1], 40)

    def test_human_readable_date(self):

        from datetime import datetime, timedelta
        now = datetime.now()
        hrago = now - timedelta(hours=1)
        yesterday = now - timedelta(days=1)
        week = now - timedelta(days=7)
        dayafter = now + timedelta(days=2)

        date = human_readable_date(hrago)

        self.failUnlessEqual(date, "an hour ago")

        date = human_readable_date(week)

        self.failUnlessEqual(date, "last week")

    def test_filmaster_recommends(self):
        """
            Test filmaster recommends
        """

        fp = FlatPage()
        fp.url = "filmaster-recommends"
        fp.title = "Title"
        fp.content = "Lorem ipsum"
        fp.save()

        flp = filmaster_recommends()
        flat_page = flp['flat_page']
        self.failUnlessEqual(flat_page.title, "Title")
        self.failUnlessEqual(flat_page.content, "Lorem ipsum")
