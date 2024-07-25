from rest_framework import serializers

from .models import Artist, Release, Track, TrackArtists, TrackFeat, TrackRemix, TrackCover


class ArtistReadSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField(source='get_aliases')

    class Meta:
        model = Artist
        fields = '__all__'
        extra_kwargs = {
            'alias': {'write_only': True},
        }


class ArtistWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()

    class Meta:
        model = Artist
        fields = '__all__'
        extra_kwargs = {
            'alias': {'read_only': True},
        }

    def validate(self, attrs):
        attrs['alias'] = Artist.build_alias(attrs.pop('aliases'))
        return attrs

    def to_representation(self, instance):
        serializer = ArtistReadSerializer(instance, context=self.context)
        return serializer.data


class ReleaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Release
        fields = '__all__'


class TrackArtistSerializer(serializers.ModelSerializer):
    artist = ArtistReadSerializer()

    class Meta:
        model = TrackArtists
        fields = ("id", "artist", "position")


class TrackReadSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_fullname")
    content_tracks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    aliases = serializers.ListField(source='get_aliases')
    artists = serializers.SerializerMethodField()
    feat = serializers.SerializerMethodField()
    remix = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        model = Track
        fields = '__all__'
        extra_kwargs = {
            'alias': {'write_only': True},
        }

    @staticmethod
    def get_artists(instance: Track):
        relations = instance.trackartists_set.all().order_by('position')
        artists: list[Artist] = list(map(lambda r: r.artist, relations))
        return ArtistReadSerializer(artists, many=True).data

    @staticmethod
    def get_feat(instance: Track):
        relations = instance.trackfeat_set.all().order_by('position')
        artists: list[Artist] = list(map(lambda r: r.artist, relations))
        return ArtistReadSerializer(artists, many=True).data

    @staticmethod
    def get_remix(instance: Track):
        relations = instance.trackremix_set.all().order_by('position')
        artists: list[Artist] = list(map(lambda r: r.artist, relations))
        return ArtistReadSerializer(artists, many=True).data

    @staticmethod
    def get_cover(instance: Track):
        relations = instance.trackcover_set.all().order_by('position')
        artists: list[Artist] = list(map(lambda r: r.artist, relations))
        return ArtistReadSerializer(artists, many=True).data


class TrackWriteSerializer(serializers.ModelSerializer):
    aliases = serializers.ListField()
    artists = serializers.ListField()
    feat = serializers.ListField()
    remix = serializers.ListField()
    cover = serializers.ListField()

    class Meta:
        model = Track
        fields = '__all__'
        extra_kwargs = {
            'alias': {'read_only': True},
        }

    def validate(self, attrs):
        attrs['alias'] = Track.build_alias(attrs.pop('aliases'))
        return attrs

    def update(self, instance: Track, validated_data) -> Track:
        def init_artists(data: list) -> list[Artist]:
            artist_ids = [item['id'] for item in data]
            artists = Artist.objects.filter(id__in=artist_ids)
            if artists.count() != len(data):
                raise serializers.ValidationError(f"Not all artists found in DB. Input: {data}. DB: {artists}")

            id_to_position = {item['id']: idx for idx, item in enumerate(data)}
            sorted_artists = sorted(artists, key=lambda artist: id_to_position[artist.id])
            return sorted_artists

        old_fullname = instance.get_fullname()
        TrackArtists.sync_relations(instance, "trackartists_set", init_artists(validated_data.pop('artists', [])))
        TrackFeat.sync_relations(instance, "trackfeat_set", init_artists(validated_data.pop('feat', [])))
        TrackRemix.sync_relations(instance, "trackremix_set", init_artists(validated_data.pop('remix', [])))
        TrackCover.sync_relations(instance, "trackcover_set", init_artists(validated_data.pop('cover', [])))
        res: Track = super().update(instance, validated_data)

        new_fullname = instance.get_fullname()
        if new_fullname != old_fullname:
            # TODO: create Note if status DOWNLOADED or IN_LIB
            pass

        return res

    def to_representation(self, instance):
        serializer = TrackReadSerializer(instance, context=self.context)
        return serializer.data
