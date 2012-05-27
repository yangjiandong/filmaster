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
# Create your views here.
from filmaster_info.register.models import *
from django.shortcuts import render_to_response
from filmaster_info.register.forms import *
from django.utils.translation import gettext_lazy as _
from django.template import RequestContext

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('register.html')
    else:
        form = RegistrationForm()
#        return render_to_response('register.html', {'form': form})
    return render_to_response('register.html', {'form': form})

def register_email_view(request):
    if request.method == "POST":
        form = RegistrationEmailForm(request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('main.html')
    else:
        form = RegistrationEmailForm()
    return render_to_response('main.html', {'form': form})   
