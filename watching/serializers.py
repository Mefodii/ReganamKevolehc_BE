from rest_framework import serializers

from .models import Group, Video, ImageModel


class ImageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = '__all__'

    def update(self, instance, validated_data):
        # Delete old image file before setting new one
        if instance.image:
            instance.image.delete()
        return super().update(instance, validated_data)


class VideoReadSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField(source='get_aliases')
    links = serializers.ListField(source='get_links')

    class Meta:
        model = Video
        fields = '__all__'
        extra_kwargs = {
            'alias': {'write_only': True},
            'links_arr': {'write_only': True},
        }


class VideoWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()
    links = serializers.ListField()

    class Meta:
        model = Video
        fields = '__all__'
        extra_kwargs = {
            'alias': {'read_only': True},
            'links_arr': {'read_only': True},
        }

    def validate(self, attrs):
        attrs['alias'] = Group.build_alias(attrs.pop('aliases'))
        attrs['links_arr'] = Group.build_links(attrs.pop('links'))
        return attrs

    def update(self, instance: Video, validated_data):
        old_order = instance.order
        res = super().update(instance, validated_data)
        instance.updated(old_order)
        return res

    def create(self, validated_data):
        instance: Video = super().create(validated_data)
        instance.created()
        return instance

    def to_representation(self, instance):
        serializer = VideoReadSerializer(instance=instance, context=self.context)
        return serializer.data


class GroupReadSerializer(serializers.ModelSerializer):
    videos = serializers.SerializerMethodField()
    images = ImageModelSerializer(many=True)
    aliases = serializers.ListField(source='get_aliases')
    links = serializers.ListField(source='get_links')

    class Meta:
        model = Group
        fields = '__all__'
        extra_kwargs = {
            'alias': {'write_only': True},
            'links_arr': {'write_only': True},
        }

    @staticmethod
    def get_videos(instance):
        videos = instance.videos.all().order_by('order')
        return VideoReadSerializer(videos, many=True).data


class GroupWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()
    links = serializers.ListField()

    class Meta:
        model = Group
        fields = '__all__'
        extra_kwargs = {
            'alias': {'read_only': True},
            'links_arr': {'read_only': True},
        }

    def validate(self, attrs):
        attrs['alias'] = Group.build_alias(attrs.pop('aliases'))
        attrs['links_arr'] = Group.build_links(attrs.pop('links'))
        return attrs

    def to_representation(self, instance):
        serializer = GroupReadSerializer(instance, context=self.context)
        return serializer.data
