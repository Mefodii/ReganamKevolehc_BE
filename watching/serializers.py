from rest_framework import serializers

from .models import Group, Video, ImageModel


class RecursiveField(serializers.ModelSerializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class ImageModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ImageModel
        fields = '__all__'


class VideoReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = '__all__'


class VideoWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = '__all__'

    def to_representation(self, instance):
        serializer = VideoReadSerializer(instance)
        return serializer.data


class GroupReadSerializer(serializers.ModelSerializer):
    videos = VideoReadSerializer(many=True)
    images = ImageModelSerializer(many=True)
    aliases = serializers.ListField(source='get_aliases')

    class Meta:
        model = Group
        fields = ('id', 'name', 'type', 'aliases', 'check_date', 'videos', 'images')


class GroupWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()

    class Meta:
        model = Group
        fields = ('id', 'name', 'aliases', 'type', 'check_date')

    def validate(self, attrs):
        attrs['alias'] = Group.build_alias(attrs.pop('aliases'))
        return attrs

    def to_representation(self, instance):
        serializer = GroupReadSerializer(instance)
        return serializer.data
