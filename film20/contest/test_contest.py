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
import unittest

from film20.core.models import Film, Person
from film20.contest.models import *
from film20.contest.contest_helper import *

from datetime import datetime
from datetime import timedelta
from django.test.client import Client

from film20.utils.test import TestCase

class ContestTestCase(TestCase):
   
    u1 = None
    u2 = None
    u3 = None
    u4 = None

    contest = None
    game1 = None
    game2 = None

    character1 = None
    character2 = None
    character3 = None
     
    def clean_data(self):
        Contest.objects.all().delete()
        User.objects.all().delete()        
        Film.objects.all().delete()

    def initialize(self):
        self.clean_data()

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()
        self.u2 = User(username='adz', email='b.orysmusielak@gmail.com')
        self.u2.save()
        self.u3 = User(username='turin', email='borysm.usielak@gmail.com')
        self.u3.save()
        self.u4 = User(username='olamus', email='borysmu.sielak@gmail.com')
        self.u4.save()

        self.contest = Contest()
        self.contest.name = "Plebiscyt"
        self.contest.start_date = datetime.now()
        self.contest.end_date = datetime.now()
        self.contest.event_status = Contest.STATUS_OPEN
        self.contest.type = Object.TYPE_CONTEST
        self.contest.permalink = "plebiscyt"
        self.contest.save()

        film1 = Film()
        film1.title = "Battlefield Earth II"
        film1.type = Object.TYPE_FILM
        film1.permalink = "/battlefirld-earth-ii/"
        film1.release_year = 2010
        film1.save()

        person1 = Person()
        person1.name = "John"
        person1.surname = "Travolta"
        person1.type = Object.TYPE_PERSON
        person1.permalink = "/john-travolta/"
        person1.save()

        person2 = Person()
        person2.name = "Tom"
        person2.surname = "Cruise"
        person2.type = Object.TYPE_PERSON
        person2.permalink = "/tom-cruise/"
        person2.save()

        person3 = Person()
        person3.name = "Forrest"
        person3.surname = "Whitaker"
        person3.type = Object.TYPE_PERSON
        person3.permalink = "/forrest-whitaker/"
        person3.save()

        character1 = Character()
        character1.character = "Scientologist 1"
        character1.person = person1
        character1.film = film1
        character1.save()
        self.character1 = character1

        character2 = Character()
        character2.character = "Scientologist 2"
        character2.person = person2
        character2.film = film1
        character2.save()
        self.character2 = character2

        character3 = Character()
        character3.character = "A non-scientologist"
        character3.person = person3
        character3.film = film1
        character3.save()
        self.character3 = character3

        today = datetime.today()
        tomorrow = today + timedelta(1)

        self.game1 = Game()
        self.game1.contest = self.contest
        self.game1.type = Object.TYPE_GAME
        self.game1.permalink = "scientologist-1-vs-scientologist-2"
        self.game1.level = Game.LEVEL_32
        self.game1.character1 = character1
        self.game1.character2 = character2
        self.game1.start_date = today
        self.game1.end_date = today
        self.game1.save()

        self.game2 = Game()
        self.game2.contest = self.contest
        self.game2.type = Object.TYPE_GAME
        self.game1.permalink = "scientologist-1-vs-scientologist-2"
        self.game2.level = Game.LEVEL_32
        self.game2.character1 = character1
        self.game2.character2 = character2
        self.game2.start_date = tomorrow
        self.game2.end_date = tomorrow
        self.game2.save()

    def test_get_current_contest(self):
        """
            Tests getting current contest
        """
        self.initialize()
        
        contest_helper = ContestHelper()
        the_contest = contest_helper.get_current_contest()
        self.assertEquals(the_contest, self.contest)

        the_contest.event_status = Contest.STATUS_CLOSED
        the_contest.save()

        self.assertRaises(NoOpenContestException, contest_helper.get_current_contest)

    def test_get_contest_by_permalink(self):
        """
            Tests getting contest by permalink
        """
        self.initialize()

        contest_helper = ContestHelper()
        the_contest = contest_helper.get_contest_by_permalink('plebiscyt')
        self.assertEquals(the_contest, self.contest)
        try:
            contest_helper.get_contest_by_permalink('plebiscyt_not_exists')
            raise Exception("NoOpenContestException should have been raised but wasn't.")
        except NoOpenContestException,e:
            pass

    def test_contest_get_game_for_date(self):
        """
            Tests if a game is retrieved for a given date and that proper
            exception is raised if game not found
        """
        self.initialize()        
        contest_helper = ContestHelper()

        # no game yesterday
        the_date = datetime.today() - timedelta(1)
        try:
            contest_helper.get_game_for_date(self.contest, the_date)
            raise Exception("No NoGameException raised!")
        except NoGameException:
            the_game = None
        self.assertEquals(the_game, None)

        # game1 today
        the_date = datetime.now()
        the_game = contest_helper.get_game_for_date(self.contest, the_date)
        self.assertEquals(the_game, self.game1)

        # game2 tomorrow
        the_date = datetime.today() + timedelta(1)
        the_game = contest_helper.get_game_for_date(self.contest, the_date)
        self.assertEquals(the_game, self.game2)

    def test_contest_get_game_by_id(self):
        """
            Tests if a game is retrieved by id and that proper
            exception is raised if game not found
        """
        self.initialize()
        contest_helper = ContestHelper()
        the_game = contest_helper.get_game_by_id(self.game1.id)
        self.assertEquals(the_game, self.game1)

        try:
            contest_helper.get_game_by_id(-1)
            raise Exception("No NoGameException raised!")
        except NoGameException:
            the_game = None
        self.assertEquals(the_game, None)

    def test_get_votes_for_character_in_game(self):
        """
            Tests the getting of all votes for a character in game
        """
        self.initialize()
        contest_helper = ContestHelper()

        # add some votes
        contest_helper.vote(self.game1, self.game1.character1, self.u1)
        contest_helper.vote(self.game1, self.game1.character1, self.u2)
        contest_helper.vote(self.game1, self.game1.character2, self.u3)

        # do the testing
        the_votes = contest_helper.get_votes_for_character_in_game(self.game1, self.character1)
        self.assertEquals(len(the_votes), 2)

        the_votes = contest_helper.get_votes_for_character_in_game(self.game1, self.character2)
        self.assertEquals(len(the_votes), 1)

    def test_voting(self):
        """
            Tests the voting on both characters in a game and retrieves results.
        """
        self.initialize()

        contest_helper = ContestHelper()

        result = contest_helper.vote(self.game1, self.game1.character1, self.u1)
        self.assertEquals(result, 0)
        result = contest_helper.vote(self.game1, self.game1.character2, self.u2)
        self.assertEquals(result, 0)
        result = contest_helper.vote(self.game1, self.game1.character2, self.u3)
        self.assertEquals(result, 0)

        the_game = contest_helper.get_game_for_date(self.contest, datetime.now())
        self.assertEquals(the_game.character1score, 1)
        self.assertEquals(the_game.character2score, 2)

        # and now some error cases
        result = contest_helper.vote(self.game2, self.game2.character1, self.u4)
        self.assertEquals(result, -1)
        result = contest_helper.vote(self.game1, self.character3, self.u4)
        self.assertEquals(result, -2)
        result = contest_helper.vote(self.game1, self.game2.character1, self.u3)
        self.assertEquals(result, -3)
        result = contest_helper.vote(self.game1, self.game2.character2, self.u3)
        self.assertEquals(result, -3)

        # just to confirm it all hasn't changed        
        the_game = contest_helper.get_game_for_date(self.contest, datetime.now())
        self.assertEquals(the_game.character1score, 1)
        self.assertEquals(the_game.character2score, 2)


    def test_get_all_games_for_contest(self):
        """
            Tests getting all games for a given contest
        """
        self.initialize()

        contest_helper = ContestHelper()
        games = contest_helper.get_all_games_for_contest("plebiscyt")
        self.assertEquals(len(games), 2)

    def test_ajax_vote(self):
        """
            Test voting for the character
        """
        self.initialize()

        client = Client()

        client.login(username=self.u1.username, password='secret')

        # sending vote
        response = client.post(self.game1.get_absolute_url()+'/json/',
                               {'game_id':self.game1.id,'character_id':self.game1.character1.id},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.failUnlessEqual(response.status_code, 200)

        # if vote was succesfull recive user avatar
        response = client.get('/'+urls["CONTEST_VOTE_AJAX"]+'/'+str(self.u1.id)+'/',
                              HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.failUnlessEqual(response.status_code, 200)

    def test_contest_get_game_by_permalink(self):
        """
            Tests if a game is retrieved by permalink and that proper
            exception is raised if game not found
        """
        self.initialize()
        contest_helper = ContestHelper()
        the_game = contest_helper.get_game_by_permalink(self.game1.permalink)
        self.assertEquals(the_game, self.game1)

        try:
            contest_helper.get_game_by_permalink("blabla")
            raise Exception("No NoGameException raised!")
        except NoGameException:
            the_game = None
        self.assertEquals(the_game, None)

