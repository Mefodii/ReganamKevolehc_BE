from django.http import JsonResponse
from .models import VIDEO_STATUS_CHOICES, VIDEO_TYPE_CHOICES, ALIAS_SEPARATOR


def get_info(request):
    info = {
        "statusTypes": [choice[0] for choice in VIDEO_STATUS_CHOICES],
        "videoTypes": dict((x.lower(), y) for x, y in VIDEO_TYPE_CHOICES),
    }
    return JsonResponse(info)
