from __future__ import annotations

from constants.enums import FileExtension
from contenting.models import ContentItem, ContentMusicItem, ContentWatcher
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo


class FileTags:
    AUTHOR = "AUTHOR"
    COPYRIGHT = "COPYRIGHT"
    COMMENT = "COMMENT"
    DISC = "DISC"
    EPISODE_ID = "EPISODE_ID"
    GENRE = "GENRE"
    TITLE = "TITLE"
    TRACK = "TRACK"

    @staticmethod
    def extract_from_youtubevideo(item: YoutubeVideo) -> dict:
        tags = {
            FileTags.TITLE: item.title,
            FileTags.TRACK: str(item.number),
            FileTags.COPYRIGHT: item.channel_name,
            FileTags.COMMENT: "by Mefodii"
        }
        if item.file_extension.is_audio():
            tags[FileTags.GENRE] = item.channel_name
            tags[FileTags.DISC] = item.video_id
        else:
            tags[FileTags.AUTHOR] = item.channel_name
            tags[FileTags.EPISODE_ID] = item.video_id

        return tags

    @staticmethod
    def extract_from_content_item(watcher: ContentWatcher, item: ContentItem | ContentMusicItem) -> dict:
        tags = {
            FileTags.TITLE: item.title,
            FileTags.TRACK: str(item.position),
            FileTags.COPYRIGHT: watcher.name,
            FileTags.COMMENT: "by Mefodii"
        }
        if FileExtension(watcher.file_extension).is_audio():
            tags[FileTags.GENRE] = watcher.name
            tags[FileTags.DISC] = item.item_id
        else:
            tags[FileTags.AUTHOR] = watcher.name
            tags[FileTags.EPISODE_ID] = item.item_id

        return tags
