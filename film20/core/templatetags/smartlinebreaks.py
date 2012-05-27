import string, re
from django.utils.functional import allow_lazy
from django.utils.safestring import SafeData, mark_safe
from django.template import Variable, Library
from django.utils.encoding import force_unicode

from film20.utils.utils import needle_in_haystack

register = Library()

def smartbreaks(value, autoescape=False):
    """Converts newlines into <p> and <br />s, but makes a paragraph only if no headline 2 exists."""
    value = re.sub(r'\r\n|\r|\n', '\n', force_unicode(value)) # normalize newlines
    paras = re.split('\n{2,}', value)
    newlist = []
    for p in paras:
        p = p.replace('\n', '<br />')
        
        if not needle_in_haystack("<h2>", p):
            p = u'<p>%s</p>' % p 
        newlist.append(p)

    # OLD CODE from linebreaks:
    #paras = [u'<p>%s</p>' % p.replace('\n', '<br />') for p in paras]

    return u'\n\n'.join(newlist)
smartbreaks = allow_lazy(smartbreaks, unicode)


def smartlinebreaks(value, autoescape=None):
    """
    Replaces line breaks in plain text with appropriate HTML; a single
    newline becomes an HTML line break (``<br />``) and a new line
    followed by a blank line becomes a paragraph break (``</p>``).
    """
    autoescape = autoescape and not isinstance(value, SafeData)
    return mark_safe(smartbreaks(value, autoescape))
smartlinebreaks.is_safe = True
smartlinebreaks.needs_autoescape = True
#smartlinebreaks = stringfilter(smartlinebreaks)

register.filter(smartlinebreaks)

