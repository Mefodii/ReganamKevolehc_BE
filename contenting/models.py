from datetime import datetime

from django.db import models
from django.db.models import Q

from django.core.validators import MinValueValidator

from constants.model_choices import CONTENT_CATEGORY_CHOICES, DOWNLOAD_STATUS_CHOICES, DOWNLOAD_STATUS_NONE, \
    CONTENT_ITEM_TYPE_CHOICES, CONTENT_WATCHER_SOURCE_TYPE_CHOICES, CONTENT_WATCHER_STATUS_CHOICES, \
    CONTENT_WATCHER_STATUS_NONE, FILE_EXTENSION_CHOICES, VIDEO_QUALITY_CHOICES, CONTENT_CATEGORY_MUSIC
from listening.models import Track
from utils.model_utils import reorder


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


class ContentItemQuerySet(models.QuerySet):
    def filter_by_content_list(self, content_list_id: int):
        if content_list_id is None:
            return self

        return self.filter(Q(content_list__pk=content_list_id))

    def filter_not_consumed(self):
        return self.filter(Q(consumed=False))


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

    objects = ContentItemQuerySet.as_manager()

    class Meta:
        abstract = True


class ContentItem(ContentItemAbstract):
    consumed = models.BooleanField(default=False)
    content_list = models.ForeignKey(ContentList, related_name="content_items", on_delete=models.CASCADE)

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
    file_extension = models.CharField(max_length=50, choices=FILE_EXTENSION_CHOICES)
    video_quality = models.IntegerField(default=None, choices=VIDEO_QUALITY_CHOICES, blank=True, null=True)
    content_list = models.OneToOneField(ContentList, related_name="content_watcher", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = ContentWatcherQuerySet.as_manager()

    def is_music(self):
        return self.category == CONTENT_CATEGORY_MUSIC

    def get_migration_position(self) -> int:
        return self.content_list.migration_position

    def get_items_count(self):
        return self.content_list.content_items.count() + self.content_list.content_music_items.count()

    def get_content_items(self):
        return self.content_list.content_items

    def get_content_music_items(self):
        return self.content_list.content_music_items

    def __str__(self):
        return (f'{self.name}{self.watcher_id} - {self.status} - {self.get_items_count()} - '
                f'{self.download} - {self.check_date}')
