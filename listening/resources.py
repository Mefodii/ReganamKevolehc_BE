from import_export import resources

from listening.models import Artist, Release, ReleaseTrack, Track


class ArtistResource(resources.ModelResource):
    class Meta:
        model = Artist


class ReleaseResource(resources.ModelResource):
    class Meta:
        model = Release


class ReleaseTrackResource(resources.ModelResource):
    class Meta:
        model = ReleaseTrack


class TrackResource(resources.ModelResource):
    class Meta:
        model = Track
