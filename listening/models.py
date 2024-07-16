from __future__ import annotations

from typing import TYPE_CHECKING, Self

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import QuerySet

from constants.enums import ReleaseType, TrackStatus
from utils.datetime_utils import default_datetime
from utils.model_utils import reorder

if TYPE_CHECKING:
    from contenting.models import ContentTrack

from listening.queryset import TrackQuerySet, ArtistQuerySet, ReleaseQuerySet, ReleaseTrackQuerySet
from utils.string_utils import normalize_text

ALIAS_SEPARATOR = ">{;}<"
ARTIST_SEPARATOR = ", "
FEAT_SEPARATOR = ", "


class Artist(models.Model):
    tracks: QuerySet[Track]
    feats: QuerySet[Track]
    remixes: QuerySet[Track]
    covers: QuerySet[Track]
    releases: QuerySet[Release]

    name = models.CharField(max_length=200)
    display_name = models.CharField(default="", max_length=200, blank=True, null=True)
    alias = models.CharField(max_length=500, blank=True)
    monitoring = models.BooleanField(default=False)
    check_date = models.DateTimeField(default=default_datetime())
    releasing = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects: ArtistQuerySet[Artist] = ArtistQuerySet.as_manager()

    def merge(self, source: Artist):
        # TODO: replace references of the source artist with self (create a Note object), then delete source object
        pass

    @staticmethod
    def clean_dead():
        objs = Artist.objects.filter_dead()
        objs.delete()

    # noinspection DuplicatedCode
    def save(self, *args, **kwargs):
        if self.name:
            self.name = normalize_text(self.name)
        if self.display_name:
            self.display_name = normalize_text(self.display_name)
        if self.alias:
            self.alias = normalize_text(self.alias)
        super().save(*args, **kwargs)

    def get_displayable_name(self):
        if self.display_name:
            return f"{self.name} ({self.display_name})"
        return self.name

    def get_aliases(self):
        if self.alias:
            return self.alias.split(ALIAS_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases: list[str]):
        return ALIAS_SEPARATOR.join(aliases)

    def __str__(self):
        return f"<{self.id}> {self.get_displayable_name()}"

    def __repr__(self):
        return str(self)


class Release(models.Model):
    tracks: QuerySet[ReleaseTrack]

    name = models.CharField(max_length=300)
    display_name = models.CharField(default="", max_length=300, blank=True, null=True)
    type = models.CharField(default=ReleaseType.OTHER.value, max_length=50, choices=ReleaseType.as_choices())
    published_at = models.DateField(null=True, blank=True)

    unknown_playlist = models.BooleanField(default=False)

    artists = models.ManyToManyField(Artist, related_name="releases")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects: ReleaseQuerySet[Release] = ReleaseQuerySet.as_manager()

    @staticmethod
    def clean_dead():
        objs = Release.objects.filter_dead()
        objs.delete()

    def save(self, *args, **kwargs):
        if self.name:
            self.name = normalize_text(self.name)
        if self.display_name:
            self.display_name = normalize_text(self.display_name)
        super().save(*args, **kwargs)

    def get_displayable_name(self):
        if self.display_name:
            return f"{self.name} ({self.display_name})"
        return self.name

    def __str__(self):
        return self.get_displayable_name()

    def __repr__(self):
        return str(self)


class Track(models.Model):
    content_tracks: QuerySet[ContentTrack]
    release_tracks: ReleaseTrackQuerySet[ReleaseTrack]

    title = models.CharField(max_length=200)
    display_title = models.CharField(default="", max_length=200, blank=True, null=True)
    alias = models.CharField(max_length=500, blank=True)
    artists = models.ManyToManyField(Artist, related_name="tracks")

    feat = models.ManyToManyField(Artist, related_name="feats")
    remix = models.ManyToManyField(Artist, related_name="remixes")
    cover = models.ManyToManyField(Artist, related_name="covers")

    #      |-> DISLIKE
    # NONE |-> MISSING
    #      |-> LIKE -> DOWNLOADED -> IN_LIBRARY
    status = models.CharField(default=TrackStatus.NONE.value, max_length=50, choices=TrackStatus.as_choices())
    is_clean = models.BooleanField(default=False)

    # TODO: temporary field, delete after all imported and all flagged True
    # True -> double check of title done for clean track / check irrelevant if is_clean = False
    double_checked = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects: TrackQuerySet[Track] = TrackQuerySet.as_manager()

    @staticmethod
    def clean_dead():
        dead = Track.objects.filter_dead()
        dead.delete()

    @staticmethod
    def clean_dcheck_dead():
        dead = Track.objects.filter_dcheck_dead()
        dead.delete()

    @classmethod
    def get_or_create_default(cls, title: str) -> Self:
        try:
            track = cls.objects.get(title=title, is_clean=False)
            return track
        except Track.DoesNotExist:
            pass

        track = cls()
        track.title = title
        track.save()

        return track

    def merge(self, source: Track):
        """
        If self is not clean, then source should also be not clean

        Obtain a new status from merging source status and self status
        References of ReleaseTrack and ContentTrack of source track are replaced with self.
        At the end, source track is deleted.

        @param source:
        @return:
        """
        if self.id is None or source.id is None:
            raise ValueError(f"Cannot perform merge when track not in DB. "
                             f"Source track: {source}. Dest track: {self}")

        if self.is_clean is False and source.is_clean is True:
            raise ValueError(f"Merge of clean source to not clean is not allowed. "
                             f"Source track: {source}. Dest track: {self}")

        if self.double_checked and source.double_checked is False:
            raise ValueError(f"Dunno how to handle merge of double_checked False to True. "
                             f"Source track: {source}. Dest track: {self}")

        source_status = TrackStatus.from_str(source.status)
        destination_status = TrackStatus.from_str(self.status)
        merged_status = TrackStatus.merge(source_status, destination_status)
        if merged_status is None:
            raise ValueError(f"Cannot merge track in DB."
                             f"Source track: {source}. Dest track: {self}")

        self.status = merged_status.value
        self.save()

        for release_track in source.release_tracks.all():
            release_track.track = self
            release_track.save()

        for content_track in source.content_tracks.all():
            content_track.track = self
            content_track.save()

        source.delete()

    # noinspection DuplicatedCode
    def save(self, *args, **kwargs):
        if self.title:
            self.title = normalize_text(self.title)
        if self.display_title:
            self.display_title = normalize_text(self.display_title)
        if self.alias:
            self.alias = normalize_text(self.alias)

        super().save(*args, **kwargs)

    def get_displayable_title(self):
        if self.display_title:
            return f"{self.title} ({self.display_title})"
        return self.title

    def get_fulltitle(self) -> str:
        fulltitle = self.get_displayable_title()
        if self.feat.exists():
            feat: Artist
            feats = FEAT_SEPARATOR.join([feat.get_displayable_name() for feat in self.feat.all()])
            fulltitle += f" [Feat. {feats}]"
        if self.remix.exists():
            remix: Artist
            remixes = FEAT_SEPARATOR.join([remix.get_displayable_name() for remix in self.remix.all()])
            fulltitle += f" (Remix by {remixes})"
        if self.cover.exists():
            cover: Artist
            covers = FEAT_SEPARATOR.join([cover.get_displayable_name() for cover in self.cover.all()])
            fulltitle += f" (Cover {covers})"

        return fulltitle

    def get_fullname(self) -> str:
        if self.id is None:
            raise ValueError(f"Cannot execute get_fullname for Track not in DB. Track: {self}")

        artist: Artist
        fullname = ""
        if self.artists.exists():  # It is possible to have no artists
            fullname += ARTIST_SEPARATOR.join([artist.get_displayable_name() for artist in self.artists.all()]) + " - "
        fullname += self.get_fulltitle()
        return fullname

    def get_aliases(self):
        if self.alias:
            return self.alias.split(ALIAS_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases):
        return ALIAS_SEPARATOR.join(aliases)

    def __str__(self):
        s = f"<{self.id}>: "
        if self.id is None:
            return s + self.get_displayable_title() + ": " + self.status

        return s + self.get_fullname() + ": " + self.status

    def __repr__(self):
        return str(self)


class ReleaseTrack(models.Model):
    position = models.IntegerField(validators=[MinValueValidator(1)])
    comment = models.CharField(default="", max_length=200, blank=True, null=True)
    needs_edit = models.BooleanField(default=False)

    release = models.ForeignKey(Release, related_name="tracks", on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name="release_tracks", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    objects: ReleaseTrackQuerySet[ReleaseTrack] = ReleaseTrackQuerySet.as_manager()

    @staticmethod
    def clean_dead():
        objs = ReleaseTrack.objects.filter_dead()
        objs.delete()

    # TODO: probably can define a class with these 4 functions, then this class will have to define field  / parent
    def reorder(self, old_position: int | None, new_position: int | None):
        reorder(self, old_position, new_position, "position", "release")

    def updated(self, old_position: int):
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self):
        self.reorder(None, self.position)

    def deleted(self):
        self.reorder(self.position, None)
