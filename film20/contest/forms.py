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
from django import forms

from film20.config.const import *

import logging
logger = logging.getLogger(__name__)

class VotingForm(forms.Form):

    game_id = forms.CharField(widget=forms.HiddenInput)
    character_id = forms.CharField(widget=forms.HiddenInput)

    the_game = None
    the_character = None

    def clean_game_id(self):
        game_id = self.cleaned_data.get('game_id', '')
        try:
            int(game_id)
            from film20.contest.contest_helper import ContestHelper
            contest_helper = ContestHelper()
            self.the_game = contest_helper.get_game_by_id(game_id)
            if self.the_game is None:
                logger.debug("Game not found for game_id="+str(game_id))
                raise forms.ValidationError(_("Game not found for game_id="+str(game_id)))
        except ValueError:
            logger.debug("game_id must be integer!")
            raise forms.ValidationError(_("game_id must be integer!"))
        return int(game_id)

    def clean_character_id(self):
        character_id = self.cleaned_data.get('character_id', '')
        try:
            int(character_id)
            from film20.contest.contest_helper import ContestHelper
            contest_helper = ContestHelper()
            self.the_character = contest_helper.get_character_from_game(self.the_game, character_id)
            logger.debug(self.the_character)
            if self.the_character is None:
                logger.debug("Character not found in game, id="+str(character_id))
                raise forms.ValidationError(_("Character not found in game, id="+str(character_id)))
        except ValueError:
            logger.debug("character_id must be integer!")
            raise forms.ValidationError(_("character_id must be integer!"))
        return int(character_id)