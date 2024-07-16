from import_export import resources

from contenting.models import ContentItem, ContentList, ContentMusicItem, ContentTrack, ContentWatcher


class ContentListResource(resources.ModelResource):
    class Meta:
        model = ContentList


class ContentItemResource(resources.ModelResource):
    class Meta:
        model = ContentItem


class ContentMusicItemResource(resources.ModelResource):
    class Meta:
        model = ContentMusicItem


class ContentTrackResource(resources.ModelResource):
    class Meta:
        model = ContentTrack


class ContentWatcherResource(resources.ModelResource):
    class Meta:
        model = ContentWatcher
