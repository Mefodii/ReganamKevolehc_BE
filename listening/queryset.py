from __future__ import annotations

from typing import Self, TYPE_CHECKING

from django.db.models import Count, Q

from utils.model_utils import TypedQuerySet

if TYPE_CHECKING:
    from listening.models import Artist


class ArtistQuerySet(TypedQuerySet):

    def filter_dead(self) -> Self:
        return self.filter(tracks__isnull=True, feats__isnull=True, remixes__isnull=True, covers__isnull=True)

    def filter_by_name_and_alias(self, value: str, case_sensitive: bool = False) -> Self:
        lookup_type = "contains" if case_sensitive else "icontains"

        filters = (
                Q(**{f"name__{lookup_type}": value}) |
                Q(**{f"alias__{lookup_type}": value})
        )

        return self.filter(filters)


class ExactArtistQuerySet(TypedQuerySet):
    def filter_exact_artists(self, artists: list[int | Artist] | set[int | Artist]) -> Self:
        pk_list = set(artists)
        if not any([isinstance(artist, int) for artist in artists]):
            pk_list = set(artist.id for artist in artists)

        query: Self = self.annotate(count=Count('artists')).filter(count=len(pk_list))

        for pk in pk_list:
            query = query.filter(artists__pk=pk)

        return query


class ReleaseQuerySet(ExactArtistQuerySet):

    def filter_dead(self) -> Self:
        return self.filter(tracks__isnull=True, unknown_playlist=False)


class TrackQuerySet(ExactArtistQuerySet):

    def filter_dead(self) -> Self:
        return self.filter(content_tracks=None, release_tracks=None, is_clean=False)

    def filter_dcheck_dead(self) -> Self:
        return self.filter_dead().filter(double_checked=False)

    def filter_fullname_contains(self, value: str, case_sensitive: bool = False) -> Self:
        lookup_type = "contains" if case_sensitive else "icontains"

        filters = (
                Q(**{f"title__{lookup_type}": value}) |
                Q(**{f"alias__{lookup_type}": value}) |
                Q(**{f"artists__name__{lookup_type}": value}) |
                Q(**{f"artists__alias__{lookup_type}": value}) |
                Q(**{f"feat__name__{lookup_type}": value}) |
                Q(**{f"feat__alias__{lookup_type}": value}) |
                Q(**{f"remix__name__{lookup_type}": value}) |
                Q(**{f"remix__alias__{lookup_type}": value}) |
                Q(**{f"cover__name__{lookup_type}": value}) |
                Q(**{f"cover__alias__{lookup_type}": value})
        )

        return self.filter(filters)


class ReleaseTrackQuerySet(TypedQuerySet):

    def filter_dead(self) -> Self:
        return self.filter(track__isnull=True)
