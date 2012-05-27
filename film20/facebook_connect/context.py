#!/usr/bin/python
#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
from film20.facebook_connect.models import *
from django.conf import settings

def facebook_connect(request):
	# FB user ID
	fcn = False
	if request.facebookconn:
		fc = request.facebookconn
		try:
			f = FBAssociation.objects.get(fb_uid=fc)
		except:
			pass
		else:
			if f.is_new:
				# if the user was autocreated allow one-time login and mail change
				fcn = True
	else:
		fc = False
	
	return {'fc': fc, 'fcn': fcn, 'connect_key': settings.FACEBOOK_CONNECT_KEY}
