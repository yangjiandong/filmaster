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

from django.db import models
from django.contrib.auth.models import User

from film20.moderation.models import ModeratedObject
from film20.moderation.registry import registry, AlreadyRegistered
from film20.moderation.items import ModeratedItem, ModeratedObjectItem

class TestModeratedObject( ModeratedObject ):
    user = models.ForeignKey( User )
    class Meta:
        permissions = (
            ( "test_moderation_permission", "Can moderate" ),
        )

class ModeratedItem1( ModeratedItem ):
    name = 'user-test'
    model = User
    permission = 'tests.test_moderation_permission'

registry.register( 
    ModeratedObjectItem( 
        TestModeratedObject, "tests.test_moderation_permission",
        name = "test-moderated-object", item_template_name='moderation/record.html'
    ) 
)
