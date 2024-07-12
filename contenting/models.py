from __future__ import annotations

from typing import Self

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, QuerySet

from constants.enums import ContentCategory, DownloadStatus, ContentItemType, ContentWatcherSourceType, FileExtension, \
    ContentWatcherStatus, VideoQuality
from contenting.queryset import ContentItemQuerySet, ContentMusicItemQuerySet, ContentListQuerySet, \
    ContentWatcherQuerySet
from listening.models import Track
from utils.datetime_utils import default_datetime
from utils.model_utils import reorder


class ContentList(models.Model):
    content_items: ContentItemQuerySet
    content_music_items: ContentMusicItemQuerySet
    content_watcher: ContentWatcher

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=ContentCategory.as_choices())
    migration_position = models.IntegerField(validators=[MinValueValidator(0)])

    objects: ContentListQuerySet[ContentList] = ContentListQuerySet.as_manager()

    def is_music(self):
        return self.category == ContentCategory.MUSIC.value

    def is_consumed(self):
        if self.is_music():
            return self.content_music_items.is_consumed()
        return self.content_items.is_consumed()

    def get_content_item(self, content_item_id: str) -> ContentItem | ContentMusicItem | None:
        try:
            items = self.content_music_items if self.is_music() else self.content_items
            return items.get(item_id=content_item_id)
        except (ContentItem.DoesNotExist, ContentMusicItem.DoesNotExist):
            return None

    def get_items_count(self):
        return self.content_items.count() + self.content_music_items.count()

    def __str__(self):
        return f'<{self.id}> {self.name}'


class ContentItemAbstract(models.Model):
    item_id = models.CharField(max_length=100, blank=True)
    url = models.CharField(max_length=500, blank=True)
    title = models.CharField(max_length=500)
    file_name = models.CharField(max_length=500, blank=True)
    position = models.IntegerField(validators=[MinValueValidator(1)])
    download_status = models.CharField(max_length=50, choices=DownloadStatus.as_choices())
    published_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ContentItem(ContentItemAbstract):
    consumed = models.BooleanField()
    content_list = models.ForeignKey(ContentList, related_name="content_items", on_delete=models.CASCADE)

    objects: ContentItemQuerySet[ContentItem] = ContentItemQuerySet.as_manager()

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
        return f'{str(self.content_list)} | <{self.id}> {self.title} - {self.position}'


class ContentMusicItem(ContentItemAbstract):
    tracks: QuerySet[ContentTrack]

    type = models.CharField(max_length=50, choices=ContentItemType.as_choices())
    content_list = models.ForeignKey(ContentList, related_name="content_music_items", on_delete=models.CASCADE)
    comment = models.CharField(default="", max_length=200, blank=True, null=True)
    parsed = models.BooleanField(default=False)

    objects: ContentMusicItemQuerySet[ContentMusicItem] = ContentMusicItemQuerySet.as_manager()

    def is_consumed(self):
        tracks_parsed = not self.tracks.filter(Q(tracks__track__isnull=False) &
                                               Q(tracks__track__like__isnull=True)).exists()
        return tracks_parsed and self.parsed

    def reorder(self, old_position: int | None, new_position: int | None):
        reorder(self, old_position, new_position, "position", "content_list")

    def updated(self, old_position: int, old_type: str, default_track: bool):
        if self.position != old_position:
            self.reorder(old_position, self.position)

        if self.type != old_type:
            if old_type == ContentItemType.PLAYLIST.value or old_type == ContentItemType.SINGLE.value:
                self.tracks.all().delete()

            if self.type == ContentItemType.SINGLE.value and default_track:
                self.generate_default_track()

    def created(self, default_track: bool):
        self.reorder(None, self.position)
        if default_track:
            self.generate_default_track()

    def generate_default_track(self):
        track = Track.get_or_create_default(self.title)
        ContentTrack.create_default_track(self, track)

    def deleted(self):
        self.reorder(self.position, None)

    def __str__(self):
        return f'{str(self.content_list)} | <{self.id}> {self.title} - {self.position}'


class ContentTrack(models.Model):
    title = models.CharField(max_length=300)
    position = models.IntegerField(validators=[MinValueValidator(1)])
    start_time = models.IntegerField(default=None, validators=[MinValueValidator(0)], blank=True, null=True)
    # Note: dunno if duration needed, maybe should be removed
    duration = models.IntegerField(default=None, validators=[MinValueValidator(0)], blank=True, null=True)
    comment = models.CharField(default="", max_length=200, blank=True, null=True)
    content_item = models.ForeignKey(ContentMusicItem, related_name="tracks", on_delete=models.CASCADE)

    needs_edit = models.BooleanField()
    is_track = models.BooleanField()
    track = models.ForeignKey(Track, related_name="content_tracks", on_delete=models.SET_NULL, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    @classmethod
    def create_default_track(cls, content_item: ContentMusicItem, track: Track) -> Self:
        if content_item.tracks.exists():
            raise ValueError(f"Cannot create default track, item already has tracks: {content_item}")

        content_track = ContentTrack()

        content_track.title = content_item.title
        content_track.content_item = content_item
        content_track.needs_edit = False
        content_track.track = track
        content_track.is_track = True
        content_track.position = 1

        content_track.save()

        return content_track

    def __str__(self):
        return f'{str(self.content_item)} | <{self.id}> {self.title} - {self.position}'

    def reorder(self, old_position: int | None, new_position: int | None):
        reorder(self, old_position, new_position, "position", "content_item")

    def updated(self, old_position: int):
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self):
        self.reorder(None, self.position)

    def deleted(self):
        self.reorder(self.position, None)


class ContentWatcher(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=ContentCategory.as_choices())
    watcher_id = models.CharField(max_length=200)
    source_type = models.CharField(max_length=50, choices=ContentWatcherSourceType.as_choices())
    status = models.CharField(max_length=50, choices=ContentWatcherStatus.as_choices())
    check_date = models.DateTimeField(default=default_datetime())
    download = models.BooleanField()
    file_extension = models.CharField(default="", max_length=50, choices=FileExtension.as_choices(),
                                      blank=True, null=True)
    video_quality = models.IntegerField(choices=VideoQuality.as_choices())
    content_list = models.OneToOneField(ContentList, related_name="content_watcher", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects: ContentWatcherQuerySet[ContentWatcher] = ContentWatcherQuerySet.as_manager()

    def is_consumed(self):
        return self.content_list.is_consumed()

    def get_content_item(self, content_item_id: str) -> ContentItem | ContentMusicItem | None:
        return self.content_list.get_content_item(content_item_id)

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
