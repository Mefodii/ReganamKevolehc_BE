from django.http import JsonResponse
from .models import CONTENT_ITEM_PART_STATUS_CHOICES, DOWNLOAD_STATUS_CHOICES, CONTENT_ITEM_TYPE_CHOICES, \
    CONTENT_WATCHER_SOURCE_TYPE_CHOICES, FILE_EXTENSION_CHOICES, CONTENT_WATCHER_STATUS_CHOICES


def get_info(request):
    info = {
        "contentItemPartStatusTypes": [choice[0] for choice in CONTENT_ITEM_PART_STATUS_CHOICES],
        "downloadStatusTypes": [choice[0] for choice in DOWNLOAD_STATUS_CHOICES],
        "contentItemTypes": [choice[0] for choice in CONTENT_ITEM_TYPE_CHOICES],
        "fileExtensionTypes": [choice[0] for choice in FILE_EXTENSION_CHOICES],
        "contentWatcherSourceTypes": [choice[0] for choice in CONTENT_WATCHER_SOURCE_TYPE_CHOICES],
        "contentWatcherStatusTypes": [choice[0] for choice in CONTENT_WATCHER_STATUS_CHOICES],
    }
    return JsonResponse(info)
