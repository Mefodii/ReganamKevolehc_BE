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
    images = ImageModelSerializer(many=True)

    class Meta:
        model = Video
        fields = '__all__'


class VideoWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Video
        fields = '__all__'


class GroupReadSerializer(serializers.ModelSerializer):
    videos = VideoReadSerializer(many=True)

    class Meta:
        model = Group
        fields = '__all__'


class GroupWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = '__all__'
