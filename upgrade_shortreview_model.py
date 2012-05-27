#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.core.models import *

oldreviews = ShortReviewOld.objects.all()
for oldreview in oldreviews:
    sr = ShortReview(                                 
        type = ShortReview.TYPE_SHORT_REVIEW,
        permalink = 'FIXME',
        status = 1,
        version = 1, 
        object=oldreview.rating.parent,
        user=oldreview.rating.user,
        review_text = oldreview.review_text,
    )
    sr.save()     
    # this is a hack so that the permalink for short review is set to object id  
    sr.permalink = str(sr.id)
    sr.save()
