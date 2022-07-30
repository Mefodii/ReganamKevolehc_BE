from rest_framework import serializers

from .models import ContentList, ContentItem, ContentItemPart, ContentWatcher


class ContentListSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentList
        fields = '__all__'


class ContentItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentItem
        fields = '__all__'


class ContentItemPartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentItemPart
        fields = '__all__'


class ContentWatcherSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentWatcher
        fields = '__all__'
