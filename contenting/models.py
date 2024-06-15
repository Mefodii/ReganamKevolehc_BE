from datetime import datetime

from django.db import models
from django.db.models import Q

from django.core.validators import MinValueValidator

from contenting.content_manager.util.constants import FILE_EXTENSION_MP3, FILE_EXTENSION_MP4, FILE_EXTENSION_MKV, \
    ALLOWED_VIDEO_QUALITY
from listening.models import Track
from utils.model_functions import reorder

CONTENT_CATEGORY_MUSIC = "Music"
CONTENT_CATEGORY_FUN = "Fun"
CONTENT_CATEGORY_GAME = "Game"
CONTENT_CATEGORY_TECH = "Tech"
CONTENT_CATEGORY_OTHER = "Other"

CONTENT_CATEGORY_CHOICES = (
    (CONTENT_CATEGORY_MUSIC, CONTENT_CATEGORY_MUSIC),
    (CONTENT_CATEGORY_FUN, CONTENT_CATEGORY_FUN),
    (CONTENT_CATEGORY_GAME, CONTENT_CATEGORY_GAME),
    (CONTENT_CATEGORY_TECH, CONTENT_CATEGORY_TECH),
    (CONTENT_CATEGORY_OTHER, CONTENT_CATEGORY_OTHER),
)

DOWNLOAD_STATUS_NONE = "NONE"
DOWNLOAD_STATUS_DOWNLOADING = "DOWNLOADING"
DOWNLOAD_STATUS_DOWNLOADED = "DOWNLOADED"
DOWNLOAD_STATUS_UNABLE = "UNABLE"
DOWNLOAD_STATUS_MISSING = "MISSING"
DOWNLOAD_STATUS_SKIP = "SKIP"

DOWNLOAD_STATUS_CHOICES = (
    (DOWNLOAD_STATUS_NONE, DOWNLOAD_STATUS_NONE),
    (DOWNLOAD_STATUS_DOWNLOADING, DOWNLOAD_STATUS_DOWNLOADING),
    (DOWNLOAD_STATUS_DOWNLOADED, DOWNLOAD_STATUS_DOWNLOADED),
    (DOWNLOAD_STATUS_UNABLE, DOWNLOAD_STATUS_UNABLE),
    (DOWNLOAD_STATUS_MISSING, DOWNLOAD_STATUS_MISSING),
    (DOWNLOAD_STATUS_SKIP, DOWNLOAD_STATUS_SKIP),
)

CONTENT_ITEM_TYPE_SINGLE = "Single"
CONTENT_ITEM_TYPE_PLAYLIST = "Playlist"
CONTENT_ITEM_TYPE_NOT_MUSIC = "NotMusic"

CONTENT_ITEM_TYPE_CHOICES = (
    (CONTENT_ITEM_TYPE_SINGLE, CONTENT_ITEM_TYPE_SINGLE),
    (CONTENT_ITEM_TYPE_PLAYLIST, CONTENT_ITEM_TYPE_PLAYLIST),
    (CONTENT_ITEM_TYPE_NOT_MUSIC, CONTENT_ITEM_TYPE_NOT_MUSIC),
)

CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE = "Youtube"
CONTENT_WATCHER_SOURCE_TYPE_BANDCAMP = "Bandcamp"
CONTENT_WATCHER_SOURCE_TYPE_OTHER = "Other"

CONTENT_WATCHER_SOURCE_TYPE_CHOICES = (
    (CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE, CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE),
    (CONTENT_WATCHER_SOURCE_TYPE_BANDCAMP, CONTENT_WATCHER_SOURCE_TYPE_BANDCAMP),
    (CONTENT_WATCHER_SOURCE_TYPE_OTHER, CONTENT_WATCHER_SOURCE_TYPE_OTHER),
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

VIDEO_QUALITY_CHOICES = [(quality, str(quality)) for quality in ALLOWED_VIDEO_QUALITY] + [("Default", None)]


class ContentListQuerySet(models.QuerySet):
    def filter_pure(self, get_pure: bool):
        """
        When get_pure is True, then return list which have no ContentWatcher
        param: get_pure: bool
        """
        if not get_pure:
            return self

        return self.filter(Q(content_watcher__isnull=True))


class ContentList(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CONTENT_CATEGORY_CHOICES)
    migration_position = models.IntegerField(default=0)

    objects = ContentListQuerySet.as_manager()

    def __str__(self):
        return f'{self.name}'


class ContentItemAbstract(models.Model):
    item_id = models.CharField(max_length=100)
    url = models.CharField(max_length=500, blank=True, null=True)
    title = models.CharField(max_length=500)
    file_name = models.CharField(max_length=500, blank=True, null=True)
    position = models.IntegerField(default=1)
    download_status = models.CharField(max_length=50, choices=DOWNLOAD_STATUS_CHOICES, blank=True,
                                       default=DOWNLOAD_STATUS_NONE)
    published_at = models.DateTimeField(default=datetime(2001, 1, 1), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ContentItemManager(models.Manager):
    def filter_by_content_list(self, content_list_id: int):
        if content_list_id is None:
            return self

        return self.filter(Q(content_list__pk=content_list_id))


class ContentItem(ContentItemAbstract):
    consumed = models.BooleanField(default=False)
    content_list = models.ForeignKey(ContentList, related_name="content_items", on_delete=models.CASCADE)

    objects = ContentItemManager()

    def reorder(self, old_position, new_position):
        reorder(self, old_position, new_position, "position", "content_list")

    def updated(self, old_position):
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self):
        self.reorder(None, self.position)

    def deleted(self):
        self.reorder(self.position, None)


class ContentMusicItem(ContentItemAbstract):
    type = models.CharField(max_length=50, choices=CONTENT_ITEM_TYPE_CHOICES)
    content_list = models.ForeignKey(ContentList, related_name="content_music_items", on_delete=models.CASCADE)

    objects = ContentItemManager()

    def __str__(self):
        return f'{str(self.content_list)}/{self.title} - {self.position}'

    def reorder(self, old_position, new_position):
        reorder(self, old_position, new_position, "position", "content_list")

    def updated(self, old_position):
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self):
        self.reorder(None, self.position)

    def deleted(self):
        self.reorder(self.position, None)


class ContentTrack(models.Model):
    name = models.CharField(max_length=300)
    # TODO: if track is mandatory field, then probably it is better to display track data instead of name
    position = models.IntegerField(default=1)
    start_time = models.IntegerField(default=0, validators=[MinValueValidator(0)], blank=True, null=True)
    duration = models.IntegerField(default=0, validators=[MinValueValidator(0)], blank=True, null=True)
    comment = models.CharField(max_length=200, blank=True, null=True)
    content_item = models.ForeignKey(ContentMusicItem, related_name="tracks", on_delete=models.CASCADE)

    needs_edit = models.BooleanField(default=False)
    like = models.BooleanField(default=None, blank=True, null=True)
    is_duplicate = models.BooleanField(default=False)
    is_track = models.BooleanField(default=True)
    track = models.ForeignKey(Track, related_name="content_tracks", on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{str(self.content_item)}/{self.name} - {self.position}'

    def reorder(self, old_position, new_position):
        reorder(self, old_position, new_position, "position", "content_item")

    def updated(self, old_position):
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self):
        self.reorder(None, self.position)

    def deleted(self):
        self.reorder(self.position, None)


class ContentWatcherQuerySet(models.QuerySet):
    def filter_by_source_type(self, source_type):
        if source_type is None:
            return self

        return self.filter(Q(source_type=source_type))


class ContentWatcher(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CONTENT_CATEGORY_CHOICES)
    watcher_id = models.CharField(max_length=200)
    source_type = models.CharField(max_length=50, choices=CONTENT_WATCHER_SOURCE_TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=CONTENT_WATCHER_STATUS_CHOICES,
                              default=CONTENT_WATCHER_STATUS_NONE)
    check_date = models.DateTimeField(default=datetime(2001, 1, 1))
    download = models.BooleanField(default=False)
    items_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    # TODO: maybe items_count is not needed (can be deducted from content_List total items)
    file_extension = models.CharField(max_length=50, choices=FILE_EXTENSION_CHOICES)
    video_quality = models.IntegerField(default=None, choices=VIDEO_QUALITY_CHOICES, blank=True, null=True)
    content_list = models.OneToOneField(ContentList, related_name="content_watcher", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = ContentWatcherQuerySet.as_manager()

    def get_migration_position(self) -> int:
        return self.content_list.migration_position

    def __str__(self):
        return f'{self.name}{self.watcher_id}'
