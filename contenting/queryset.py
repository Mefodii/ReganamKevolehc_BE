from __future__ import annotations

from typing import Self

from django.db.models import Q

from constants.enums import ContentCategory
from utils.model_utils import TypedQuerySet


class ContentListQuerySet(TypedQuerySet):
    def filter_pure(self, get_pure: bool):
        """
        When get_pure is True, then return list which have no ContentWatcher
        param: get_pure: bool
        """
        if not get_pure:
            return self

        return self.filter(Q(content_watcher__isnull=True))


class ContentItemAbstractQuerySet(TypedQuerySet):
    def filter_by_content_list(self, content_list_id: int) -> Self:
        if content_list_id is None:
            return self

        return self.filter(content_list__pk=content_list_id)


class ContentItemQuerySet(ContentItemAbstractQuerySet):

    def filter_not_consumed(self) -> Self:
        return self.filter(consumed=False)

    def filter_by_title(self, value: str, case_sensitive: bool = False) -> Self:
        lookup_type = "contains" if case_sensitive else "icontains"
        filters = (Q(**{f"title__{lookup_type}": value}))

        return self.filter(filters)

    def is_consumed(self) -> bool:
        return not self.filter_not_consumed().exists()


class ContentMusicItemQuerySet(ContentItemAbstractQuerySet):

    def filter_not_consumed(self) -> Self:
        return self.filter(parsed=False)

    def is_consumed(self) -> bool:
        return not self.filter_not_consumed().exists()


class ContentWatcherQuerySet(TypedQuerySet):
    def filter_by_source_type(self, source_type):
        if source_type is None:
            return self

        return self.filter(source_type=source_type)

    def get_passive(self) -> Self:
        return self.filter(download=False).order_by('name')

    def get_active_audio(self) -> Self:
        return self.filter(download=True, category=ContentCategory.MUSIC.value).order_by('name')

    def get_active_video(self) -> Self:
        return self.filter(download=True).exclude(category=ContentCategory.MUSIC.value).order_by('name')
