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
"""
A script which removes expired/inactive user accounts from the
database.

This is intended to be run as a cron job; for example, to have it run
at midnight each Sunday, you could add lines like the following to
your crontab::

    DJANGO_SETTINGS_MODULE=yoursite.settings
    0 0 * * sun python /path/to/registration/bin/delete_expired_users.py

See the method ``delete_expired_users`` of the ``RegistrationManager``
class in ``registration/models.py`` for further documentation.

"""

if __name__ == '__main__':
    from registration.models import RegistrationProfile
    RegistrationProfile.objects.delete_expired_users()
