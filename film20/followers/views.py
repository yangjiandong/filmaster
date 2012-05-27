# Create your views here.
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from film20.config.urls import *
from film20.followers.models import Followers
from film20.utils.utils import json_error, json_return
#from django.db import transaction

import logging
logger = logging.getLogger(__name__)

@login_required
#@transaction.commit_on_success
def follow(request, ajax=None):
    if request.method == "POST":
        try:
            user_id = int(request.POST.get("user_id"))
            user_to_follow = get_object_or_404(User, id=user_id)
            follow_val = int(request.POST.get("follow_val"))
            next = str(request.POST.get("next"))
            if follow_val == Followers.UNKNOWN:
                request.user.followers.remove(user_to_follow)
            if follow_val == Followers.FOLLOWING:
                request.user.followers.follow(user_to_follow)
            if ajax=="json":
                context = {
                        'success': True,
                        'data': request.user.id,
                    }
                logger.debug("Sending ajax response.")
                return json_return(context)
            else:
                return HttpResponseRedirect(next)
        except:
            if ajax=="json":
                return json_error()
            else:
                raise Http404

@login_required
def follower_partial(request, user_id):

    if request.user.id == int(user_id):
        logger.debug("Sending avatar.")
        return render_to_response(
            'followers/follower_partial.html',
            {
                'user':request.user,
            },
            context_instance=RequestContext(request)
        )
    else:
        logger.debug('User id invalid!')
        raise Http404
