from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

from watching.models import Video, Group, ImageModel


@admin.register(Video)
class VideoAdmin(ImportExportModelAdmin):
    pass


@admin.register(Group)
class GroupAdmin(ImportExportModelAdmin):
    pass


@admin.register(ImageModel)
class ImageModelAdmin(ImportExportModelAdmin):
    pass
