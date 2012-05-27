# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext
from film20.register.forms import RegistrationForm
from film20.config.urls import templates
from django.contrib.auth.models import User
from film20.register.models import RegistrationModel

def registration_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            register = form.save(commit=False)
            if request.user.is_authenticated():
                register.user = request.user
                user = User.objects.get(id=request.user.id)
                if user.email is None:
                    user.email = register.email
                    user.save()
            register.save()
            return render_to_response(templates['REGISTER'], context_instance=RequestContext(request))
    else:
        form = None
        if request.user.is_authenticated():
            try:
                register = RegistrationModel.objects.get(user=request.user)
            except  RegistrationModel.DoesNotExist:
                form = RegistrationForm()
        else:
            form = RegistrationForm()

    return render_to_response(templates['REGISTER'], {'form': form}, context_instance=RequestContext(request))
