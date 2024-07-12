from rest_framework import viewsets, permissions

from constants.constants import RequestType
from utils.drf_utils import MultiSerializerViewSet, MediumResultsSetPagination
from .models import Artist, Release, Track
from .serializers import ArtistSerializer, ReleaseSerializer, TrackReadSerializer, TrackWriteSerializer


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ArtistSerializer


class ReleaseViewSet(viewsets.ModelViewSet):
    queryset = Release.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ReleaseSerializer


class TrackViewSet(MultiSerializerViewSet):
    queryset = Track.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializers = {
        RequestType.DEFAULT.value: TrackWriteSerializer,
        RequestType.LIST.value: TrackReadSerializer,
        RequestType.RETRIEVE.value: TrackReadSerializer,
    }
    pagination_class = MediumResultsSetPagination

    # TODO: get tracks by artistid

    def get_queryset(self):
        return self.queryset.order_by("id")
