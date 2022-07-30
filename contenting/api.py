from django.http import Http404
from rest_framework.response import Response

from .models import ContentList, ContentItem, ContentItemPart, ContentWatcher
from rest_framework import viewsets, permissions
from .serializers import ContentListSerializer, ContentItemSerializer, ContentItemPartSerializer, \
    ContentWatcherSerializer


class ContentListViewSet(viewsets.ModelViewSet):
    queryset = ContentList.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ContentListSerializer


class ContentItemViewSet(viewsets.ModelViewSet):
    queryset = ContentItem.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ContentItemSerializer


class ContentItemPartViewSet(viewsets.ModelViewSet):
    queryset = ContentItemPart.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ContentItemPartSerializer


class ContentWatcherViewSet(viewsets.ModelViewSet):
    queryset = ContentWatcher.objects.all()
    permission_classes = [
        permissions.AllowAny
    ]
    serializer_class = ContentWatcherSerializer

