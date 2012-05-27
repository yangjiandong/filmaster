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
from django.shortcuts import render_to_response, Http404, get_object_or_404
from django.template import RequestContext

#from film20.contest.models import Contest, Game
from film20.contest.exceptions import NoOpenContestException, NoGameException
from film20.contest.contest_helper import ContestHelper
from film20.contest.forms import VotingForm
from film20.config.urls import *
from film20.utils.utils import JSONResponse, json_error, json_return

import logging
logger = logging.getLogger(__name__)
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect


def show_contest(request, contest_permalink=None):
    """
      Schedule for character contest
    """
    the_contest = None
    the_games = None
    contest_helper = ContestHelper()
    try:
        if contest_permalink is None:
            the_contest = contest_helper.get_current_contest()
        else:
            the_contest = contest_helper.get_contest_by_permalink(contest_permalink)

        the_games = contest_helper.get_all_games_for_contest(the_contest.permalink)
        level32, level16, level8, quarter_final, semi_final, final = contest_helper.get_games_by_level(the_games)
    except NoOpenContestException, e:
        raise Http404

    return render_to_response(
        templates['SHOW_CONTEST'],
        {
            'the_contest': the_contest,
            'the_games': the_games,
            'level32': level32,
            'level16': level16,
            'level8': level8,
            'quarter_final': quarter_final,
            'semi_final': semi_final,
            'final': final,
        },
        context_instance=RequestContext(request)
    )


def show_game(request, contest_permalink=None, game_permalink=None, ajax=None):
    """
        Simple view that show a single game with options to
                vote for the characters
    """

    the_contest = None
    the_game_vote = None
    contest_helper = ContestHelper()

    if request.POST:
        if (not request.user.is_authenticated()):
            if ajax==None:
                return HttpResponseRedirect(full_url('LOGIN') + '?next=%s' % request.path)
            elif ajax=='json':
                return json_error("LOGIN")
        voting_form = VotingForm(request.POST)
        if voting_form is not None:
            logger.debug("Voting form submitted.")
            if voting_form.is_valid():
                logger.debug("Voting form valid.")
                contest_helper.vote(voting_form.the_game, voting_form.the_character, request.user)
                if ajax == "json":
                    context = {
                            'success': True,
                            'data': request.user.id,
                        }
                    logger.debug("Sending ajax response.")
                    return json_return(context)
            else:
                logger.debug("Voting form invalid.")
        else:
            logger.debug("Voting form not submitted.")

    try:
        if contest_permalink is None:
            the_contest = contest_helper.get_current_contest()
        else:
            the_contest = contest_helper.get_contest_by_permalink(contest_permalink)

        if game_permalink is None:
            the_game = contest_helper.get_game_for_date(the_contest, datetime.today())
        else:
            the_game = contest_helper.get_game_by_permalink(game_permalink)
        if request.user.is_authenticated():
            the_game_vote = contest_helper.get_vote_for_game(the_game, request.user)
        votes_for_character1 = contest_helper.get_votes_for_character_in_game(the_game, the_game.character1)
        votes_for_character2 = contest_helper.get_votes_for_character_in_game(the_game, the_game.character2)
        if the_game_vote is None:
            voting_form1 = contest_helper.prepare_voting_form1(the_game)
            voting_form2 = contest_helper.prepare_voting_form2(the_game)
        else:
            # no need for forms if already voted
            voting_form1 = None
            voting_form2 = None
    except NoOpenContestException, e:
        raise Http404
    except NoGameException, e:
        raise Http404

    return render_to_response(
            templates['SHOW_GAME'],
            {
                'the_contest': the_contest,
                'the_game': the_game,
                'voting_form1': voting_form1,
                'voting_form2': voting_form2,
                'the_game_vote': the_game_vote,
                'votes_for_character1': votes_for_character1,
                'votes_for_character2': votes_for_character2,
            },
            context_instance=RequestContext(request)
        )

@login_required
def show_game_ajax(request, user_id):

    if request.user.id == int(user_id):
        logger.debug("Sending avatar.")
        return render_to_response(
            templates['SHOW_GAME_AJAX'],
            {
                'user':request.user,
            },
            context_instance=RequestContext(request)
        )
    else:
        logger.debug('User id invalid!')
        raise Http404
