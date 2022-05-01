from import_export import resources
from watching.models import Group, Video, ImageModel


class GroupResource(resources.ModelResource):
    class Meta:
        model = Group


class VideoResource(resources.ModelResource):
    class Meta:
        model = Video


class ImageModelResource(resources.ModelResource):
    class Meta:
        model = ImageModel
