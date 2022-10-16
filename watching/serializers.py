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

    class Meta:
        model = Video
        fields = '__all__'
        extra_kwargs = {'alias': {'write_only': True}}


class VideoWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()

    class Meta:
        model = Video
        fields = '__all__'
        extra_kwargs = {'alias': {'read_only': True}}

    def validate(self, attrs):
        attrs['alias'] = Group.build_alias(attrs.pop('aliases'))
        return attrs

    def update(self, instance, validated_data):
        old_order = instance.order
        new_order = validated_data["order"]
        if old_order != new_order:
            instance.reorder(old_order, new_order)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.created()
        return instance

    def to_representation(self, instance):
        serializer = GroupReadSerializer(instance=instance.group, context=self.context)
        return serializer.data


class GroupReadSerializer(serializers.ModelSerializer):
    videos = VideoReadSerializer(many=True)
    images = ImageModelSerializer(many=True)
    aliases = serializers.ListField(source='get_aliases')

    class Meta:
        model = Group
        fields = '__all__'
        extra_kwargs = {'alias': {'write_only': True}}


class GroupWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()

    class Meta:
        model = Group
        fields = '__all__'
        extra_kwargs = {'alias': {'read_only': True}}

    def validate(self, attrs):
        attrs['alias'] = Group.build_alias(attrs.pop('aliases'))
        return attrs

    def to_representation(self, instance):
        serializer = GroupReadSerializer(instance, context=self.context)
        return serializer.data
