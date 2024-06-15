from django.http import JsonResponse
from .models import WATCHING_STATUS_CHOICES, WATCHING_TYPE_CHOICES, WATCHING_AIR_STATUS_CHOICES


def get_info(request):
    info = {
        "statusTypes": [choice[0] for choice in WATCHING_STATUS_CHOICES],
        "airStatusTypes": [choice[0] for choice in WATCHING_AIR_STATUS_CHOICES],
        "watchingTypes": dict((x.lower(), y) for x, y in WATCHING_TYPE_CHOICES),
    }
    return JsonResponse(info)
