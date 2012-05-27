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
from django.utils.translation import ugettext as _

from film20.tagging.managers import ModelTaggedItemManager, TagDescriptor

VERSION = (0, 3, 'pre')

class AlreadyRegistered(Exception):
    """
    An attempt was made to register a model more than once.
    """
    pass

registry = []

def register(model, tag_descriptor_attr='tags',
             tagged_item_manager_attr='tagged'):
    """
    Sets the given model class up for working with tags.
    """
    if model in registry:
        raise AlreadyRegistered(
            _('The model %s has already been registered.') % model.__name__)
    registry.append(model)

    # Add tag descriptor
    setattr(model, tag_descriptor_attr, TagDescriptor())

    # Add custom manager
    ModelTaggedItemManager().contribute_to_class(model,
                                                 tagged_item_manager_attr)
