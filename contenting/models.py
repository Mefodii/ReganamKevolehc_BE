from datetime import datetime

from django.db import models
from django.db.models import Q

from django.core.validators import MinValueValidator

from contenting.content_manager.util.constants import FILE_EXTENSION_MP3, FILE_EXTENSION_MP4, FILE_EXTENSION_MKV
from listening.models import Track

CONTENT_ITEM_PART_STATUS_ADD = "ADD"
CONTENT_ITEM_PART_STATUS_SKIP = "SKIP"
CONTENT_ITEM_PART_STATUS_DUPLICATE = "DUPLICATE"

CONTENT_ITEM_PART_STATUS_CHOICES = (
    (CONTENT_ITEM_PART_STATUS_ADD, CONTENT_ITEM_PART_STATUS_ADD),
    (CONTENT_ITEM_PART_STATUS_SKIP, CONTENT_ITEM_PART_STATUS_SKIP),
    (CONTENT_ITEM_PART_STATUS_DUPLICATE, CONTENT_ITEM_PART_STATUS_DUPLICATE),
)

DOWNLOAD_STATUS_DOWNLOADED = "DOWNLOADED"
DOWNLOAD_STATUS_UNABLE = "UNABLE"
DOWNLOAD_STATUS_MISSING = "MISSING"

DOWNLOAD_STATUS_CHOICES = (
    (DOWNLOAD_STATUS_DOWNLOADED, DOWNLOAD_STATUS_DOWNLOADED),
    (DOWNLOAD_STATUS_UNABLE, DOWNLOAD_STATUS_UNABLE),
    (DOWNLOAD_STATUS_MISSING, DOWNLOAD_STATUS_MISSING),
)

CONTENT_ITEM_TYPE_SINGLE = "Single"
CONTENT_ITEM_TYPE_PLAYLIST = "Playlist"

CONTENT_ITEM_TYPE_CHOICES = (
    (CONTENT_ITEM_TYPE_SINGLE, CONTENT_ITEM_TYPE_SINGLE),
    (CONTENT_ITEM_TYPE_PLAYLIST, CONTENT_ITEM_TYPE_PLAYLIST),
)

CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE = "Youtube"
CONTENT_WATCHER_SOURCE_TYPE_BANDCAMP = "Bandcamp"

CONTENT_WATCHER_SOURCE_TYPE_CHOICES = (
    (CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE, CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE),
    (CONTENT_WATCHER_SOURCE_TYPE_BANDCAMP, CONTENT_WATCHER_SOURCE_TYPE_BANDCAMP),
)

FILE_EXTENSION_CHOICES = (
    (FILE_EXTENSION_MP3, FILE_EXTENSION_MP3),
    (FILE_EXTENSION_MP4, FILE_EXTENSION_MP4),
    (FILE_EXTENSION_MKV, FILE_EXTENSION_MKV),
)

CONTENT_WATCHER_STATUS_WAITING = "Waiting"
CONTENT_WATCHER_STATUS_RUNNING = "Running"
CONTENT_WATCHER_STATUS_FINISHED = "Finished"
CONTENT_WATCHER_STATUS_WARNING = "Warning"
CONTENT_WATCHER_STATUS_ERROR = "Error"
CONTENT_WATCHER_STATUS_DEAD = "Dead"
CONTENT_WATCHER_STATUS_NONE = "None"

CONTENT_WATCHER_STATUS_CHOICES = (
    (CONTENT_WATCHER_STATUS_WAITING, CONTENT_WATCHER_STATUS_WAITING),
    (CONTENT_WATCHER_STATUS_RUNNING, CONTENT_WATCHER_STATUS_RUNNING),
    (CONTENT_WATCHER_STATUS_FINISHED, CONTENT_WATCHER_STATUS_FINISHED),
    (CONTENT_WATCHER_STATUS_WARNING, CONTENT_WATCHER_STATUS_WARNING),
    (CONTENT_WATCHER_STATUS_ERROR, CONTENT_WATCHER_STATUS_ERROR),
    (CONTENT_WATCHER_STATUS_DEAD, CONTENT_WATCHER_STATUS_DEAD),
    (CONTENT_WATCHER_STATUS_NONE, CONTENT_WATCHER_STATUS_NONE),
)


class ContentList(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.name}'


class ContentItem(models.Model):
    item_id = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    file_name = models.CharField(max_length=500)
    number = models.IntegerField(default=1)
    inspected = models.BooleanField(default=False)
    parsed = models.BooleanField(default=False)
    download_status = models.CharField(max_length=50, choices=DOWNLOAD_STATUS_CHOICES)
    type = models.CharField(max_length=50, choices=CONTENT_ITEM_TYPE_CHOICES)
    content_list = models.ForeignKey(ContentList, related_name="content_items", on_delete=models.CASCADE)
    published_at = models.DateTimeField(default=datetime(2001, 1, 1), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class ContentItemPart(models.Model):
    start_time = models.CharField(max_length=30)
    comment = models.CharField(max_length=500)
    status = models.CharField(max_length=50, choices=CONTENT_ITEM_PART_STATUS_CHOICES)
    content_item = models.ForeignKey(ContentItem, related_name="content_parts", on_delete=models.CASCADE)
    needs_edit = models.BooleanField(default=False)
    track = models.ForeignKey(Track, related_name="content_parts", on_delete=models.CASCADE, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)


class ContentWatcherQuerySet(models.QuerySet):
    def filter_by_source_type(self, source_type):
        if source_type is None:
            return self

        return self.filter(Q(source_type=source_type))


class ContentWatcher(models.Model):
    name = models.CharField(max_length=200)
    watcher_id = models.CharField(max_length=200)
    source_type = models.CharField(max_length=50, choices=CONTENT_WATCHER_SOURCE_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=CONTENT_WATCHER_STATUS_CHOICES)
    check_date = models.DateTimeField(default=datetime(2001, 1, 1))
    download_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    file_extension = models.CharField(max_length=50, choices=FILE_EXTENSION_CHOICES)
    content_list = models.OneToOneField(ContentList, related_name="content_watcher", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = ContentWatcherQuerySet.as_manager()

    def __str__(self):
        return f'{self.name}{self.watcher_id}'
