from .models import Artist, Release, Track
from rest_framework import viewsets, permissions
from .serializers import ArtistSerializer, ReleaseSerializer, TrackSerializer


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


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = TrackSerializer

