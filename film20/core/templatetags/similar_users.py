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

from django.template import Library, TemplateSyntaxError
from film20.recommendations.recom_helper import RecomHelper
from django.conf import settings
from core.models import User

register = Library()
import logging
logger = logging.getLogger(__name__)

@register.inclusion_tag('dashboard/similar_users_tag.html', takes_context=True)
def similar_users(context, arg):
    """ displays widget with similar users"""

    more = False
    if not isinstance(arg, User):
        user = User.objects.get(username__iexact=arg)
    else:
        user = arg

    logged_user = context['request'].user
    is_logged = logged_user.username == user.username

    page_size = getattr(settings, "NUMBER_OF_SIMILAR_USERS_ON_TAG", 3)
    recom_helper = RecomHelper()
    filmaster_type = 'all'
    similar_users = recom_helper.get_best_tci_users(user=user, limit=page_size+1, filmaster_type=filmaster_type)

    list_of_users = list(similar_users)
    list_of_shown_users  = list(similar_users[:settings.NUMBER_OF_SIMILAR_USERS_ON_TAG])

    if len(list_of_users) > len(list_of_shown_users):
        more = True

    return {
        'users': similar_users[:settings.NUMBER_OF_SIMILAR_USERS_ON_TAG],
        'more': more,
        'user_checked': user,
        'is_logged': is_logged,
    }



