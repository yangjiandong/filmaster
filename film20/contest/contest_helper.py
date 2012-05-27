#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2010 Filmaster (Borys Musielak, Adam Zielinski).
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
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django import forms

from film20.contest.models import Contest, Game, GameVote
from film20.contest.exceptions import NoOpenContestException, NoGameException
from film20.contest.forms import VotingForm
from film20.utils.cache_helper import get_cache, set_cache, delete_cache, CACHE_VOTES_FOR_CHARACTER_IN_GAME

import logging
logger = logging.getLogger(__name__)
from datetime import datetime


class ContestHelper:
    """
    A ``Helper`` contest for objects, to facilitate common static operations
    """

    # TODO: ajax voting
    # TODO: method for getting all the games in order (for the table)

    def get_contest_by_permalink(self, contest_permalink):
        """
            Returns the contest with given permalink
        """
        the_contest = None
        try:
            the_contest = Contest.objects.get(
                permalink=contest_permalink
                )
        except Contest.DoesNotExist:
            logger.debug("No open Contest exists with permalink %s" % contest_permalink)
            raise NoOpenContestException()

        return the_contest

    def get_current_contest(self):
        """
            Returns the current open contest
        """
        the_contest = None
        try:
            the_contest = Contest.objects.get(
                event_status=Contest.STATUS_OPEN
                )
        except Contest.DoesNotExist:
            logger.debug("No Contest exists.")
            raise NoOpenContestException()

        return the_contest


    def get_game_for_date(self, the_contest, the_date):
        """
            Returns the game for the given date and contest
            or None if no game is scheduled.
        """
        the_game = None
        try:
            the_game = Game.objects.get(
                contest=the_contest,
                start_date__lte=the_date,
                end_date__gte=the_date,
                )
        except Game.DoesNotExist:
            logger.debug("Game does not exisis for this contest and date.")
            raise NoGameException()

        return the_game

    def get_game_by_id(self, game_id):
        """
            Returns the game with the given id
        """
        the_game = None
        try:
            the_game = Game.objects.get(
                id=game_id
                )
        except Game.DoesNotExist:
            logger.debug("Game with such id does not exist: " + str(game_id))
            raise NoGameException()

        return the_game

    def get_game_by_permalink(self, game_permalink):
        """
           Returns the game with given permalink
        """
        the_game = None
        try:
            the_game = Game.objects.get(
                permalink = game_permalink
            )
        except Game.DoesNotExist:
            logger.debug("Game with such permalink does not exist: " + str(game_permalink))
            raise NoGameException()

        return the_game

    # TODO: write a test
    def get_character_from_game(self, game, character_id):
        """
            Gets the character with the given id, provided that it's
            one of the characters in the game
        """
        if game is None:
            return None
        elif game.character1.id == int(character_id):
            return game.character1
        elif game.character2.id == int(character_id):
            return game.character2
        else:
            return None

    def vote(self, the_game, the_character, the_user):
        """
            Adds a single vote for the selected character in the game.
            If game is scheduled for a different day than today, it ignores
            the request.
        """

        try:
            from datetime import datetime
            today =  datetime.today()
            Game.objects.get(
                id=the_game.id,
                start_date__lte=today,
                end_date__gte=today,
                )
        except Game.DoesNotExist:
            logger.debug("Game does not exisist for this contest and date.")
            return -1

        if(the_character.id==the_game.character1.id):
            the_game.character1score = the_game.character1score + 1
        elif (the_character.id==the_game.character2.id):
            the_game.character2score = the_game.character2score + 1
        else:
            logger.debug("The character doesn't match any characted in the game!")
            #TODO: throw an exception
            return -2

        # if we're here it means we have found the game
        try:
            GameVote.objects.get(
                game=the_game,
                user=the_user,
                )
            logger.debug("The user have already voted for this game!")
            return -3
        except GameVote.DoesNotExist:
            # this is good
            pass

        # apply the vote
        vote = GameVote()
        vote.character = the_character
        vote.game = the_game
        vote.user = the_user
        vote.save() # this should never fail now as we check for a duplicate vote above
        logger.debug("Vote counted!")

        delete_cache(CACHE_VOTES_FOR_CHARACTER_IN_GAME, "%s_%s" % (the_game.id, the_character.id))

        # if successful, it means we have voted, so now we can update the
        # vote count for given character in game as well
        the_game.save()

        return 0

    # TODO: write a test
    def get_vote_for_game(self, the_game, the_user):
        try:
            game_vote = GameVote.objects.get(
                game=the_game,
                user=the_user,
                )
            logger.debug("The user has already voted for this game!")
            return game_vote
        except GameVote.DoesNotExist:
            # this ok good
            logger.debug("The user hasn't voted for this game, yet!")
            return None

    # TODO: write a test that tests the contents of the cache after retrieving votes and then voting again (should be empty)
    def get_votes_for_character_in_game(self, the_game, the_character):
        """
            Retrieves a list of votes for the given character in the given game.
            Gets it from cache if present (cache is cleared when voting)
        """
        result = get_cache(CACHE_VOTES_FOR_CHARACTER_IN_GAME, "%s_%s" % (the_game.id, the_character.id))
        if result!=None:
            return result
        game_votes = GameVote.objects.filter(
            game=the_game,
            character=the_character,
        )
        set_cache(CACHE_VOTES_FOR_CHARACTER_IN_GAME,
                  "%s_%s" % (the_game.id, the_character.id),
                  game_votes)
        return game_votes

    # TODO: write a test
    def prepare_voting_form1(self, the_game):
        return self.__prepare_voting_form(the_game, the_game.character1)

    def prepare_voting_form2(self, the_game):
        return self.__prepare_voting_form(the_game, the_game.character2)

    def __prepare_voting_form(self, the_game, the_character):
        today = datetime.today().date()
        if the_game.start_date <= today and the_game.end_date >= today:
            return VotingForm(
                initial= {
                    'game_id' : the_game.id,
                    'character_id' : the_character.id,
                }
            )
        else:
            return None

    def get_all_games_for_contest(self, contest_permalink):
        """
            Gets all games for contest
        """
        games = Game.objects.filter(
            contest__permalink=contest_permalink,
        )
        games = games.order_by("-start_date")

        return games

    def get_games_by_level(self, games):
        """
           Gets games by level
        """
        level32 = filter(lambda x:x.level == Game.LEVEL_32, games)
        level16 = filter(lambda x:x.level == Game.LEVEL_16, games)
        level8 = filter(lambda x:x.level == Game.LEVEL_8, games)
        quarter_final = filter(lambda x:x.level == Game.QUARTER_FINAL, games)
        semi_final = filter(lambda x:x.level == Game.SEMI_FINAL, games)
        final = filter(lambda x:x.level == Game.FINAL, games)

        return level32, level16, level8, quarter_final, semi_final, final