from film20.merging_tools.forms import ReportPersonDuplicateForm
from film20.merging_tools.models import DuplicatePerson, DuplicateFilm

from film20.utils.template import Library

register = Library()

@register.simple_tag
def people_to_merge_count():
    return DuplicatePerson.objects.filter( resolved=False ).count()

@register.simple_tag
def movies_to_merge_count():
    return DuplicateFilm.objects.filter( resolved=False ).count()
