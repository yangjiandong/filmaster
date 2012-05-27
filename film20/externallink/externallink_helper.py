from django.db.models import Q
from film20.externallink.models import ExternalLink
from django.conf import settings

MAX_EXTERNAL_LINKS = getattr(settings, 'MAX_EXTERNAL_LINKS', 5)

def get_videos_for_movie(permalink):
    external_videos = ExternalLink.objects.filter(
                                                  Q(film__permalink=permalink),
                                                  Q(status = ExternalLink.PUBLIC_STATUS),
                                                  Q(url_kind=ExternalLink.VIDEO)|
                                                  Q(url_kind=ExternalLink.TRAILER)|
                                                  Q(url_kind=ExternalLink.FULL_FEATURE)|
                                                  Q(url_kind=ExternalLink.OTHER_VIDEO)).order_by("-created_at")
    if external_videos:
        return external_videos[0:2]

def get_links_for_movie(permalink):
    external_links = ExternalLink.objects.filter(Q(film__permalink=permalink),
                                                         Q(status = ExternalLink.PUBLIC_STATUS),
                                                         Q(url_kind=ExternalLink.REVIEW)|
                                                         Q(url_kind=ExternalLink.BOOK)|
                                                         Q(url_kind=ExternalLink.NEWS)).order_by("-created_at")[:MAX_EXTERNAL_LINKS]
    return external_links
