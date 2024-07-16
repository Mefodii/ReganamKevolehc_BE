from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from contenting.models import ContentList, ContentWatcher, ContentItem, ContentMusicItem, ContentTrack


@admin.register(ContentList)
class ContentListAdmin(ImportExportModelAdmin):
    pass


@admin.register(ContentWatcher)
class ContentWatcherAdmin(ImportExportModelAdmin):
    pass


@admin.register(ContentItem)
class ContentItemAdmin(ImportExportModelAdmin):
    pass


@admin.register(ContentMusicItem)
class ContentMusicItemAdmin(ImportExportModelAdmin):
    pass


@admin.register(ContentTrack)
class ContentTrackAdmin(ImportExportModelAdmin):
    pass
