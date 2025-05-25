from __future__ import annotations

from itertools import zip_longest
from typing import TYPE_CHECKING, Self

from django.db import models
from django.db.models import QuerySet

from constants.constants import MODEL_LIST_SEPARATOR, TEST_OBJ_ANNOTATION
from constants.enums import ReleaseType, TrackStatus
from utils.datetime_utils import default_datetime
from utils.model_utils import PositionedModel

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

    name = models.CharField(max_length=200, unique=True)
    alias = models.CharField(max_length=500, blank=True)
    monitoring = models.BooleanField(default=False)
    check_date = models.DateTimeField(default=default_datetime())
    releasing = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # noinspection PyClassVar
    objects: ArtistQuerySet[Artist] = ArtistQuerySet.as_manager()

    def is_test_object(self) -> bool:
        return self.name.startswith(TEST_OBJ_ANNOTATION)

    def get_aliases(self):
        if self.alias:
            return self.alias.split(MODEL_LIST_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases):
        return MODEL_LIST_SEPARATOR.join(aliases)

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
        if self.alias:
            self.alias = normalize_text(self.alias)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"<{self.id}> {self.name}"

    def __repr__(self):
        return str(self)


class Release(models.Model):
    tracks: QuerySet[ReleaseTrack]

    name = models.CharField(max_length=300)
    type = models.CharField(default=ReleaseType.OTHER.value, max_length=50, choices=ReleaseType.as_choices())
    published_at = models.DateField(null=True, blank=True)

    unknown_playlist = models.BooleanField(default=False)

    artists = models.ManyToManyField(Artist, related_name="releases", through="ReleaseArtists")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # noinspection PyClassVar
    objects: ReleaseQuerySet[Release] = ReleaseQuerySet.as_manager()

    @staticmethod
    def clean_dead():
        objs = Release.objects.filter_dead()
        objs.delete()

    def save(self, *args, **kwargs):
        if self.name:
            self.name = normalize_text(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class ReleaseArtists(PositionedModel):
    parent_name = "track"
    release = models.ForeignKey(Release, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)


class Track(models.Model):
    content_tracks: QuerySet[ContentTrack]
    release_tracks: ReleaseTrackQuerySet[ReleaseTrack]

    title = models.CharField(max_length=200)
    alias = models.CharField(max_length=500, blank=True)
    artists = models.ManyToManyField(Artist, related_name="tracks", through="TrackArtists")
    feat = models.ManyToManyField(Artist, related_name="feats", through="TrackFeat")
    remix = models.ManyToManyField(Artist, related_name="remixes", through="TrackRemix")
    cover = models.ManyToManyField(Artist, related_name="covers", through="TrackCover")

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

    # noinspection PyClassVar
    objects: TrackQuerySet[Track] = TrackQuerySet.as_manager()

    def is_test_object(self) -> bool:
        return self.title.startswith(TEST_OBJ_ANNOTATION)

    def get_aliases(self):
        if self.alias:
            return self.alias.split(MODEL_LIST_SEPARATOR)
        return []

    @staticmethod
    def build_alias(aliases):
        return MODEL_LIST_SEPARATOR.join(aliases)

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
        If self is not clean, then the source should also be not clean

        Get a new status from merging source status and status of self
        References of ReleaseTrack and ContentTrack of source track are replaced with self.
        At the end, the source track is deleted.

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
        if self.alias:
            self.alias = normalize_text(self.alias)

        super().save(*args, **kwargs)

    def get_fulltitle(self) -> str:
        fulltitle = self.title
        if self.feat.exists():
            feat: Artist
            feats = FEAT_SEPARATOR.join([m2m.artist.name for m2m in self.trackfeat_set.all().order_by("position")])
            fulltitle += f" [Feat. {feats}]"
        if self.remix.exists():
            remix: Artist
            remixes = FEAT_SEPARATOR.join([m2m.artist.name for m2m in self.trackremix_set.all().order_by("position")])
            fulltitle += f" (Remix by {remixes})"
        if self.cover.exists():
            cover: Artist
            covers = FEAT_SEPARATOR.join([m2m.artist.name for m2m in self.trackcover_set.all().order_by("position")])
            fulltitle += f" (Cover {covers})"

        return fulltitle

    def get_fullname(self) -> str:
        if self.id is None:
            raise ValueError(f"Cannot execute get_fullname for Track not in DB. Track: {self}")

        artist: Artist
        fullname = ""
        if self.artists.exists():  # It is possible to have no artists
            fullname += ARTIST_SEPARATOR.join(
                [m2m.artist.name for m2m in self.trackartists_set.all().order_by("position")]) + " - "
        fullname += self.get_fulltitle()
        return fullname

    def __str__(self):
        s = f"<{self.id}>: "
        if self.id is None:
            return s + self.title + ": " + self.status

        return s + self.get_fullname() + ": " + self.status

    def __repr__(self):
        return str(self)


class TrackArtistM2MAbstract(PositionedModel):
    parent_name = "track"
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @classmethod
    def sync_relations(cls, track: Track, relations_name: str,
                       new_relations: list[Artist] | ArtistQuerySet[Artist]) -> bool:
        old_relations: list[Self] = getattr(track, relations_name).all().order_by("position")
        changed: bool = False
        zipped = zip_longest(old_relations, new_relations, fillvalue=None)
        for position, (m2m, artist) in enumerate(zipped, start=1):
            m2m: Self | None
            artist: Artist | None

            if m2m is None:
                cls.objects.create(track=track, artist=artist, position=position)
                changed = True
            elif artist is None:
                m2m.delete()
                changed = True
            else:
                if m2m.artist.id == artist.id:
                    continue

                if m2m.position != position:
                    raise ValueError(f"Position mismatch. Has {m2m.position}. Got: {position}. Relation: {m2m}")

                m2m.artist = artist
                m2m.save()
                changed = True

        return changed

    def __str__(self):
        return f'<{self.id}> {self.position} - {self.track} - {self.artist}'

    def __repr__(self):
        return str(self)


class TrackArtists(TrackArtistM2MAbstract):
    pass


class TrackFeat(TrackArtistM2MAbstract):
    pass


class TrackRemix(TrackArtistM2MAbstract):
    pass


class TrackCover(TrackArtistM2MAbstract):
    pass


class ReleaseTrack(PositionedModel):
    parent_name = "release"

    comment = models.CharField(default="", max_length=200, blank=True, null=True)
    needs_edit = models.BooleanField(default=False)

    release = models.ForeignKey(Release, related_name="tracks", on_delete=models.CASCADE)
    track = models.ForeignKey(Track, related_name="release_tracks", on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # noinspection PyClassVar
    objects: ReleaseTrackQuerySet[ReleaseTrack] = ReleaseTrackQuerySet.as_manager()

    @staticmethod
    def clean_dead():
        objs = ReleaseTrack.objects.filter_dead()
        objs.delete()
