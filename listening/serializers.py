from rest_framework import serializers

from .models import Artist, Release, Track


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = '__all__'


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'


class TrackReadSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_fullname")
    content_tracks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Track
        fields = '__all__'


class TrackWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Track
        fields = '__all__'
