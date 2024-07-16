from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from listening.models import Artist, Release, Track, ReleaseTrack


@admin.register(Artist)
class ArtistAdmin(ImportExportModelAdmin):
    pass


@admin.register(Release)
class ReleaseAdmin(ImportExportModelAdmin):
    pass


@admin.register(Track)
class TrackAdmin(ImportExportModelAdmin):
    pass


@admin.register(ReleaseTrack)
class ReleaseTrack(ImportExportModelAdmin):
    pass
