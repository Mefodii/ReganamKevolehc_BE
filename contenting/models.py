from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from constants.enums import ContentCategory, DownloadStatus, ContentItemType, ContentWatcherSourceType, FileExtension, \
    ContentWatcherStatus, VideoQuality
from listening.models import Track
from utils.datetime_utils import default_datetime
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
    category = models.CharField(max_length=50, choices=ContentCategory.as_choices())
    migration_position = models.IntegerField(validators=[MinValueValidator(0)])

    objects = ContentListQuerySet.as_manager()

    def is_music(self):
        return self.category == ContentCategory.MUSIC.value

    def is_consumed(self):
        if self.is_music():
            t = self.content_music_items.filter(tracks__consumed=False)
            print(t)
            return t.exists() is False
        return self.content_items.filter(consumed=False).exists() is False

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
    item_id = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=500, blank=True)
    title = models.CharField(max_length=500)
    file_name = models.CharField(max_length=500, blank=True)
    position = models.IntegerField(validators=[MinValueValidator(0)])
    download_status = models.CharField(max_length=50, choices=DownloadStatus.as_choices())
    published_at = models.DateTimeField(default=default_datetime(), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = ContentItemQuerySet.as_manager()

    class Meta:
        abstract = True


class ContentItem(ContentItemAbstract):
    consumed = models.BooleanField()
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
    type = models.CharField(max_length=50, choices=ContentItemType.as_choices())
    content_list = models.ForeignKey(ContentList, related_name="content_music_items", on_delete=models.CASCADE)

    def is_consumed(self):
        return self.tracks.filter(consumed=False).exists() is False

    def reorder(self, old_position, new_position):
        reorder(self, old_position, new_position, "position", "content_list")

    def updated(self, old_position):
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self):
        self.reorder(None, self.position)

    def deleted(self):
        self.reorder(self.position, None)

    def __str__(self):
        return f'{str(self.content_list)}/{self.title} - {self.position}'


class ContentTrack(models.Model):
    name = models.CharField(max_length=300)
    position = models.IntegerField(validators=[MinValueValidator(0)])
    start_time = models.IntegerField(default=None, validators=[MinValueValidator(0)], blank=True, null=True)
    duration = models.IntegerField(default=None, validators=[MinValueValidator(0)], blank=True, null=True)
    comment = models.CharField(max_length=200, blank=True)
    content_item = models.ForeignKey(ContentMusicItem, related_name="tracks", on_delete=models.CASCADE)
    consumed = models.BooleanField()

    needs_edit = models.BooleanField()
    like = models.BooleanField(default=None, blank=True, null=True)
    is_duplicate = models.BooleanField()
    is_track = models.BooleanField()
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
    category = models.CharField(max_length=50, choices=ContentCategory.as_choices())
    watcher_id = models.CharField(max_length=200)
    source_type = models.CharField(max_length=50, choices=ContentWatcherSourceType.as_choices())
    status = models.CharField(max_length=50, choices=ContentWatcherStatus.as_choices())
    check_date = models.DateTimeField(default=default_datetime())
    download = models.BooleanField()
    file_extension = models.CharField(max_length=50, choices=FileExtension.as_choices(), blank=True, null=True)
    video_quality = models.IntegerField(choices=VideoQuality.as_choices())
    content_list = models.OneToOneField(ContentList, related_name="content_watcher", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects = ContentWatcherQuerySet.as_manager()

    def is_consumed(self):
        return self.content_list.is_consumed()

    def is_music(self):
        return self.category == ContentCategory.MUSIC.value

    def get_migration_position(self) -> int:
        return self.content_list.migration_position

    def get_items_count(self):
        return self.get_content_items().count() + self.get_content_music_items().count()

    def get_content_items(self):
        return self.content_list.content_items

    def get_content_music_items(self):
        return self.content_list.content_music_items

    def __str__(self):
        return (f'{self.name}{self.watcher_id} - {self.status} - {self.get_items_count()} - '
                f'{self.download} - {self.check_date}')
