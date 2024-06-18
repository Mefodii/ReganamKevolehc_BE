from pprint import pprint

from django.core.management.base import BaseCommand

from constants import paths
from constants.model_choices import CONTENT_CATEGORY_OTHER, CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE, \
    CONTENT_WATCHER_STATUS_FINISHED, DOWNLOAD_STATUS_NONE, DOWNLOAD_STATUS_UNABLE, DOWNLOAD_STATUS_DOWNLOADED, \
    DOWNLOAD_STATUS_MISSING, DOWNLOAD_STATUS_SKIP
from contenting.models import ContentWatcher, ContentItem
from contenting.reganam_tnetnoc.model.file_extension import FileExtension
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItem
from contenting.reganam_tnetnoc.utils import yt_datetime
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from contenting.reganam_tnetnoc.watchers.youtube.watcher import YoutubeWatcher
from contenting.serializers import ContentWatcherCreateSerializer

DOWNLOAD_STATUS_MAPPING = {
    YoutubeVideo.STATUS_NO_STATUS: DOWNLOAD_STATUS_NONE,
    YoutubeVideo.STATUS_UNABLE: DOWNLOAD_STATUS_UNABLE,
    YoutubeVideo.STATUS_DOWNLOADED: DOWNLOAD_STATUS_DOWNLOADED,
    YoutubeVideo.STATUS_MISSING: DOWNLOAD_STATUS_MISSING,
    YoutubeVideo.STATUS_SKIP: DOWNLOAD_STATUS_SKIP,
}


def get_or_create_content_watcher(watcher: YoutubeWatcher) -> ContentWatcher:
    try:
        content_watcher = ContentWatcher.objects.get(watcher_id=watcher.channel_id)
        return content_watcher
    except ContentWatcher.DoesNotExist:
        cw_data = {
            "name": watcher.name,
            "category": CONTENT_CATEGORY_OTHER,  # NOTE: set category manually after import
            "watcher_id": watcher.channel_id,
            "source_type": CONTENT_WATCHER_SOURCE_TYPE_YOUTUBE,
            "status": CONTENT_WATCHER_STATUS_FINISHED,
            "check_date": watcher.check_date,
            "download": False,
            "file_extension": watcher.file_extension,
        }
        cw_serializer = ContentWatcherCreateSerializer(data=cw_data)
        if cw_serializer.is_valid():
            instance = cw_serializer.create(cw_serializer.validated_data)
            return instance
        else:
            raise Exception(cw_serializer.errors)


def get_or_create_content_item(content_watcher: ContentWatcher, db_video: YoutubeVideo,
                               playlist_item: PlaylistItem) -> ContentItem:
    try:
        content_item = ContentItem.objects.get(item_id=db_video.video_id)
    except ContentItem.DoesNotExist:
        content_item = ContentItem()

    content_item.item_id = db_video.video_id
    content_item.url = db_video.get_url()
    content_item.title = db_video.title
    content_item.file_name = db_video.file_name if content_watcher.download else None
    content_item.position = db_video.number
    content_item.download_status = DOWNLOAD_STATUS_MAPPING[db_video.status]
    content_item.published_at = yt_datetime.yt_to_py(db_video.published_at)
    content_item.content_list = content_watcher.content_list
    content_item.consumed = playlist_item.item_flag == PlaylistItem.ITEM_FLAG_CONSUMED
    content_item.save()

    return content_item


class Command(BaseCommand):
    def handle(self, **options):
        watchers_file = paths.YOUTUBE_WATCHERS_PATH
        watchers: list[YoutubeWatcher] = YoutubeWatcher.from_file(watchers_file)
        for watcher in watchers:
            content_watcher = get_or_create_content_watcher(watcher)

            if content_watcher.download and content_watcher.file_extension == FileExtension.MP3:
                # TODO: import as music items
                ...
            else:
                if not watcher.db_videos.is_sorted():
                    raise ValueError(f"Watcher has videos not sorted. Watcher: {watcher}")
                video_items = watcher.db_videos.get_sorted()
                for video_item in video_items:
                    playlist_item = watcher.playlist_items.get_by_url(video_item.get_url())
                    content_item = get_or_create_content_item(content_watcher, video_item, playlist_item)
