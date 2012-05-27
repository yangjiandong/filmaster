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

class NoOpenContestException(Exception):
    """
       Exception thrown when there is no open contest at the time of
       calling a method to retrieve it.
    """
    pass

class NoGameException(Exception):
    """
        Exception thrown when trying to retrieve a game that does not exist
        (either by ID or by date and contest)
    """
    pass