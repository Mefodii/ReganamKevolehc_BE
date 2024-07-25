from rest_framework import serializers

from listening.serializers import TrackReadSerializer
from .models import ContentList, ContentItem, ContentTrack, ContentWatcher, ContentMusicItem


class ContentListSerializer(serializers.ModelSerializer):
    content_watcher = serializers.PrimaryKeyRelatedField(many=False, read_only=True)
    items_count = serializers.IntegerField(source="get_items_count", read_only=True)
    consumed = serializers.BooleanField(source="is_consumed", read_only=True)

    class Meta:
        model = ContentList
        fields = '__all__'


class ContentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentItem
        fields = '__all__'

    def update(self, instance: ContentItem, validated_data) -> ContentItem:
        old_position = instance.position
        res = super().update(instance, validated_data)
        instance.updated(old_position=old_position)
        return res

    def create(self, validated_data) -> ContentItem:
        instance: ContentItem = super().create(validated_data)
        instance.created()
        return instance


class ContentMusicItemWriteSerializer(serializers.ModelSerializer):
    single_track = serializers.IntegerField(default=None, allow_null=True)

    class Meta:
        model = ContentMusicItem
        fields = '__all__'

    def update(self, instance: ContentMusicItem, validated_data) -> ContentMusicItem:
        # TODO: do not allow to set parsed to true if has any tracks which are not parsed (clean = False, like = None)
        old_position = instance.position
        old_type = instance.type

        res = super().update(instance, validated_data)
        instance.updated(old_position=old_position, old_type=old_type,
                         single_track=validated_data.pop("single_track", None))
        return res

    def create(self, validated_data) -> ContentMusicItem:
        single_track = validated_data.pop('single_track', None)
        instance: ContentMusicItem = super().create(validated_data)
        instance.created(single_track=single_track)
        return instance

    def to_representation(self, instance):
        serializer = ContentMusicItemReadSerializer(instance, context=self.context)
        return serializer.data


class ContentMusicItemReadSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()

    class Meta:
        model = ContentMusicItem
        fields = '__all__'

    @staticmethod
    def get_tracks(instance):
        tracks = instance.tracks.all().order_by('position')
        return ContentTrackReadSerializer(tracks, many=True).data


class ContentTrackReadSerializer(serializers.ModelSerializer):
    track = serializers.SerializerMethodField()

    class Meta:
        model = ContentTrack
        fields = '__all__'

    @staticmethod
    def get_track(instance: ContentTrack):
        if instance.track:
            return TrackReadSerializer(instance.track).data
        return None


class ContentTrackWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTrack
        fields = '__all__'

    def update(self, instance: ContentTrack, validated_data) -> ContentTrack:
        old_position = instance.position
        res = super().update(instance, validated_data)
        instance.updated(old_position=old_position)
        return res

    def create(self, validated_data) -> ContentTrack:
        instance: ContentTrack = super().create(validated_data)
        instance.created()
        return instance

    def to_representation(self, instance: ContentTrack):
        serializer = ContentTrackReadSerializer(instance, context=self.context)
        return serializer.data


class ContentWatcherSerializer(serializers.ModelSerializer):
    migration_position = serializers.IntegerField(source="get_migration_position")
    items_count = serializers.IntegerField(source="get_items_count")
    consumed = serializers.BooleanField(source="is_consumed")

    class Meta:
        model = ContentWatcher
        fields = '__all__'

    def update(self, instance: ContentWatcher, validated_data) -> ContentWatcher:
        if instance.name != validated_data['name'] or instance.category != validated_data['category']:
            content_list_instance: ContentList = instance.content_list
            content_list_instance.name = validated_data['name']
            content_list_instance.category = validated_data['category']
            content_list_instance.save()

        res = super().update(instance, validated_data)
        return res


class ContentWatcherCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentWatcher
        exclude = ('content_list',)

    def create(self, validated_data) -> ContentWatcher:
        if validated_data.get('content_list', None) is None:
            content_list_data = {
                "name": validated_data['name'],
                "category": validated_data['category'],
                "migration_position": 0
            }
            serializer = ContentListSerializer(data=content_list_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            content_list_instance = serializer.create(serializer.validated_data)
            validated_data['content_list'] = content_list_instance
        instance: ContentWatcher = super().create(validated_data)
        return instance

    def to_representation(self, instance):
        serializer = ContentWatcherSerializer(instance=instance, context=self.context)
        return serializer.data
