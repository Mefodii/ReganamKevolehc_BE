from django.http import Http404
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from constants.constants import RequestType
from utils.drf_utils import MultiSerializerViewSet, LargeResultsSetPagination
from .models import ContentList, ContentItem, ContentTrack, ContentWatcher, ContentMusicItem, ContentItemQuerySet
from .serializers import ContentListSerializer, ContentItemSerializer, ContentTrackReadSerializer, \
    ContentWatcherSerializer, ContentMusicItemWriteSerializer, ContentMusicItemReadSerializer, \
    ContentTrackWriteSerializer, ContentWatcherCreateSerializer

QPARAM_CONTENT_LIST = "contentList"
QPARAM_CONTENT_LIST_PURE = "getCLP"
QPARAM_HIDE_CONSUMED = "hideConsumed"


class ContentListViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ContentListSerializer

    def get_queryset(self):
        get_pure = self.request.query_params.get(QPARAM_CONTENT_LIST_PURE, "false") == "true"
        return ContentList.objects.filter_pure(get_pure)


class ContentItemViewSet(viewsets.ModelViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ContentItemSerializer
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        objects: ContentItemQuerySet = ContentItem.objects.get_queryset()
        content_list = self.request.query_params.get(QPARAM_CONTENT_LIST, None)
        hide_consumed = self.request.query_params.get(QPARAM_HIDE_CONSUMED, "false") == "true"

        if self.request.method == "GET" and content_list is None:
            raise ValidationError(f"Missing query param: {QPARAM_CONTENT_LIST}")

        objects = objects.filter_by_content_list(content_list)
        if hide_consumed:
            objects = objects.filter_not_consumed()

        return objects.order_by('position')

    # noinspection PyMethodMayBeStatic
    def put(self, request, *args, **kwargs):
        # Note 2024.06.15: Have not used ListSerializer because of deadlock situation.
        # - Update function for single object requires validated_data (which requires content_list as instance)
        # - If passing validated_data for all request.data to ListSerializer, all ids are lost and cannot build
        #   the map of instance <-> validated_data for single object
        instance_ids = [item['id'] for item in request.data]
        instances_map = {instance.id: instance for instance in ContentItem.objects.filter(id__in=instance_ids)}

        # Check that all items exists in DB
        for item in request.data:
            if instances_map.get(item["id"]) is None:
                return Response({'errors': f"Item not found: {str(item)}"}, status=status.HTTP_400_BAD_REQUEST)

        serializers = [ContentItemSerializer(instance=instances_map.get(data["id"]), data=data) for data in
                       request.data]

        # Validation
        for serializer in serializers:
            if not serializer.is_valid():
                return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Update
        updated_instances: list[ContentItem] = []
        try:
            for serializer in serializers:
                updated_instances.append(serializer.save())
        except Exception as e:
            return Response({'errors': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ContentItemSerializer(updated_instances, many=True).data)

    def delete(self, request, *args, **kwargs):

        objects: list[ContentItem] = []
        for content_item_id in request.data:
            try:
                objects.append(ContentItem.objects.get(pk=content_item_id))
            except ContentItem.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND, data=content_item_id)

        for content_item in objects:
            content_item.deleted()
            self.perform_destroy(content_item)

        return Response(status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        data = {}
        try:
            instance: ContentItem = self.get_object()
            instance.deleted()
            self.perform_destroy(instance)
            data = ContentItemSerializer(instance, context=self.get_serializer_context()).data
            response_status = status.HTTP_200_OK
        except Http404:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(status=response_status, data=data)


class ContentMusicItemViewSet(MultiSerializerViewSet):
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        RequestType.DEFAULT.value: ContentMusicItemWriteSerializer,
        RequestType.LIST.value: ContentMusicItemReadSerializer,
        RequestType.RETRIEVE.value: ContentMusicItemReadSerializer,
    }

    def get_queryset(self):
        objects: ContentItemQuerySet = ContentMusicItem.objects.get_queryset()
        content_list = self.request.query_params.get(QPARAM_CONTENT_LIST, None)
        return objects.filter_by_content_list(content_list).order_by('position')

    def destroy(self, request, *args, **kwargs):
        data = {}
        try:
            instance: ContentMusicItem = self.get_object()
            instance.deleted()
            self.perform_destroy(instance)
            data = ContentMusicItemReadSerializer(instance, context=self.get_serializer_context()).data
            response_status = status.HTTP_200_OK
        except Http404:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(status=response_status, data=data)


class ContentTrackViewSet(MultiSerializerViewSet):
    queryset = ContentTrack.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        RequestType.DEFAULT.value: ContentTrackWriteSerializer,
        RequestType.LIST.value: ContentTrackReadSerializer,
        RequestType.RETRIEVE.value: ContentTrackReadSerializer,
    }

    def destroy(self, request, *args, **kwargs):
        data = {}
        try:
            instance: ContentTrack = self.get_object()
            instance.deleted()
            self.perform_destroy(instance)
            data = ContentTrackReadSerializer(instance, context=self.get_serializer_context()).data
            response_status = status.HTTP_200_OK
        except Http404:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(status=response_status, data=data)


class ContentWatcherViewSet(MultiSerializerViewSet):
    queryset = ContentWatcher.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        RequestType.DEFAULT.value: ContentWatcherSerializer,
        RequestType.CREATE.value: ContentWatcherCreateSerializer,
    }

    def destroy(self, request, *args, **kwargs):
        data = {}
        try:
            instance: ContentWatcher = self.get_object()
            data = ContentWatcherSerializer(instance=instance,
                                            context=self.get_serializer_context()).data
            content_list_instance = instance.content_list
            content_list_instance.delete()
            response_status = status.HTTP_200_OK
        except Http404:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(status=response_status, data=data)
