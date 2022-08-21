from django.http import Http404
from rest_framework.response import Response

from .models import Group, Video, ImageModel
from rest_framework import viewsets, permissions, status
from .serializers import VideoWriteSerializer, VideoReadSerializer, ImageModelSerializer, \
    GroupReadSerializer, GroupWriteSerializer

LIST = "list"
RETRIEVE = "retrieve"
CREATE = "create"
UPDATE = "update"
PARTIAL_UPDATE = "partial_update"
DEFAULT = "default"

QPARAM_VIDEO_TYPE = "videoType"


class MultiSerializerViewSet(viewsets.ModelViewSet):
    serializers = {
        DEFAULT: None,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers[DEFAULT])


class GroupViewSet(MultiSerializerViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        DEFAULT: GroupWriteSerializer,
        LIST: GroupReadSerializer,
        RETRIEVE: GroupReadSerializer,
    }

    def get_queryset(self):
        video_type = self.request.query_params.get(QPARAM_VIDEO_TYPE, None)
        return Group.objects.filter_by_type(video_type)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            # Delete existing image files before deleting group
            images = instance.images.all()
            for image_instance in images:
                if image_instance.image:
                    image_instance.image.delete()

            self.perform_destroy(instance)
        except Http404:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class VideoViewSet(MultiSerializerViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        DEFAULT: VideoWriteSerializer,
        LIST: VideoReadSerializer,
        RETRIEVE: VideoReadSerializer,
    }

    def get_queryset(self):
        video_type = self.request.query_params.get(QPARAM_VIDEO_TYPE, None)
        return Video.objects.filter_by_type(video_type)


class ImageModelViewSet(viewsets.ModelViewSet):
    queryset = ImageModel.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ImageModelSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.image:
                instance.image.delete()
        except Http404:
            print("Failed to delete image file: ", self.get_object())
            return Response(status=status.HTTP_404_NOT_FOUND)
        return super().destroy(request, *args, **kwargs)

