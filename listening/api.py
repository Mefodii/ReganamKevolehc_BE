from .models import Artist, Album, Track
from rest_framework import viewsets, permissions
from .serializers import ArtistSerializer, AlbumSerializer, TrackSerializer


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ArtistSerializer


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = AlbumSerializer


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = TrackSerializer

