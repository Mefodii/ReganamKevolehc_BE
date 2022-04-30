from django.http import JsonResponse
from .models import WATCHIO_STATUS_CHOICES, WATCHIO_TYPE_CHOICES, WATCHIO_AIR_STATUS_CHOICES


def get_info(request):
    info = {
        "statusTypes": [choice[0] for choice in WATCHIO_STATUS_CHOICES],
        "airStatusTypes": [choice[0] for choice in WATCHIO_AIR_STATUS_CHOICES],
        "watchioTypes": dict((x.lower(), y) for x, y in WATCHIO_TYPE_CHOICES),
    }
    return JsonResponse(info)
