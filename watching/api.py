from django.http import Http404
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from constants.constants import RequestType
from utils.drf_utils import MultiSerializerViewSet
from .models import Group, Video, ImageModel, VideoManager, GroupManager
from .serializers import VideoWriteSerializer, VideoReadSerializer, ImageModelSerializer, \
    GroupReadSerializer, GroupWriteSerializer

QPARAM_WATCHING_TYPE = "watchingType"
QPARAM_GROUP = "group"


class GroupViewSet(MultiSerializerViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        RequestType.DEFAULT.value: GroupWriteSerializer,
        RequestType.LIST.value: GroupReadSerializer,
        RequestType.RETRIEVE.value: GroupReadSerializer,
    }

    def get_queryset(self):
        video_type = self.request.query_params.get(QPARAM_WATCHING_TYPE, None)
        objects: GroupManager = Group.objects
        return objects.filter_by_type(video_type)

    def destroy(self, request, *args, **kwargs):
        try:
            instance: Group = self.get_object()

            # Delete existing image files before deleting group
            images: list[ImageModel] = instance.images.all()
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
        RequestType.DEFAULT.value: VideoWriteSerializer,
        RequestType.LIST.value: VideoReadSerializer,
        RequestType.RETRIEVE.value: VideoReadSerializer,
    }

    def get_queryset(self):
        video_type = self.request.query_params.get(QPARAM_GROUP, None)
        objects: VideoManager = Video.objects
        return objects.filter_by_group(video_type).order_by('order')

    def destroy(self, request, *args, **kwargs):
        data = {}
        try:
            instance: Video = self.get_object()
            instance.deleted()
            self.perform_destroy(instance)
            data = VideoReadSerializer(instance, context=self.get_serializer_context()).data
            response_status = status.HTTP_200_OK
        except Http404:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(status=response_status, data=data)


class ImageModelViewSet(viewsets.ModelViewSet):
    queryset = ImageModel.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ImageModelSerializer

    def destroy(self, request, *args, **kwargs):
        try:
            instance: ImageModel = self.get_object()
            if instance.image:
                instance.image.delete()
        except Http404:
            print("Failed to delete image file: ", self.get_object())
            return Response(status=status.HTTP_404_NOT_FOUND)
        return super().destroy(request, *args, **kwargs)
