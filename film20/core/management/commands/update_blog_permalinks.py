# -*- coding: utf-8 -*-

import re

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from film20.useractivity.models import UserActivity

class Command( BaseCommand ):

    def handle( self, *args, **options ):
        user = User.objects.get( username="blog" )
        for useractivity in UserActivity.objects.filter( user=user, permalink__isnull=False ):
            m = re.match ( '^http://filmaster.filmaster.(.*)', useractivity.permalink )
            if m:
                useractivity.permalink = "http://blog.filmaster." + m.group( 1 )
                useractivity.save()
