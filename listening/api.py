from rest_framework import viewsets, permissions

from constants.constants import RequestType
from utils.drf_utils import MultiSerializerViewSet, MediumResultsSetPagination
from .models import Artist, Release, Track
from .serializers import ArtistSerializer, ReleaseSerializer, TrackReadSerializer, TrackWriteSerializer

QPARAM_TRACK_SEARCH = "trackSearch"
QPARAM_SEARCH_CASE_SENSITIVE = "caseSensitive"


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

    def get_queryset(self):
        objects = Track.objects.all()

        case_sensitive = self.request.query_params.get(QPARAM_SEARCH_CASE_SENSITIVE, "false") == "true"
        track_search = self.request.query_params.get(QPARAM_TRACK_SEARCH, "")
        if track_search:
            objects = objects.filter_fullname_contains(track_search, case_sensitive)

        return objects.order_by('id')
