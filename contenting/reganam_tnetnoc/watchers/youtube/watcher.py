from __future__ import annotations

from typing import Self

from constants import paths
from contenting.reganam_tnetnoc.model.file_extension import FileExtension
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItemList
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeAPIItem
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo, YoutubeVideoList
from utils import file, datetime_utils

WATCHER_NAME = "watcher_name"
CHANNEL_ID = "channel_id"
CHECK_DATE = "check_date"
VIDEO_COUNT = "video_count"
FILE_EXTENSION = "file_extension"
VIDEO_QUALITY = "video_quality"
PLAYLIST_FILE = "playlist_file"
DOWNLOAD = "download"

DUMMY_NAME = "dummy_name"

MANDATORY_FIELDS = [
    WATCHER_NAME,
    CHANNEL_ID,
    FILE_EXTENSION,
    CHECK_DATE,
    VIDEO_COUNT,
    DOWNLOAD,
]


class YoutubeWatcher:
    def __init__(self, name: str, channel_id: str, check_date: str, video_count: int, file_extension: FileExtension,
                 download: bool, playlist_file: str | None = None, video_quality: int | None = None):
        self.is_dummy = name == DUMMY_NAME

        if " " in name:
            raise ValueError(f"Space not allowed in name. Name: {name}")

        self.name = name
        self.channel_id = channel_id
        self.check_date: str = check_date
        self.video_count = video_count
        self.file_extension = file_extension
        self.download = download

        self.playlist_file = playlist_file
        self.playlist_items: PlaylistItemList = PlaylistItemList([])
        if playlist_file:
            self.playlist_items: PlaylistItemList = PlaylistItemList.from_file(playlist_file, empty_if_not_found=True)
        self.video_quality = video_quality

        self.save_location: str = "\\".join([paths.WATCHERS_DOWNLOAD_PATH, self.name])
        self.db_file: str = "\\".join([paths.WATCHER_JSON_DB_PATH, self.name + ".txt"])

        self.videos: list[YoutubeVideo] = []
        self.missing_videos: list[YoutubeVideo] = []
        self.changed_videos: list[tuple[YoutubeVideo, YoutubeVideo]] = []
        self.api_videos: list[YoutubeAPIItem] = []
        self.db_videos: YoutubeVideoList = YoutubeVideoList.from_file(self.db_file, empty_if_not_found=True)
        self.new_check_date: str | None = None

    @classmethod
    def dummy(cls) -> Self:
        obj = YoutubeWatcher(DUMMY_NAME, "dummy", "", 0, FileExtension.MP3,
                             True, None, None)
        return obj

    @staticmethod
    def validate_data(data: dict):
        for field in MANDATORY_FIELDS:
            if data.get(field) is None:
                raise ValueError(f"{field} not found")

    def append_video(self, yt_video: YoutubeVideo) -> None:
        self.videos.append(yt_video)

    def init_video(self, api_video: YoutubeAPIItem) -> YoutubeVideo:
        video_id = api_video.get_id()
        title = api_video.get_title()
        channel_name = self.name
        published_at = api_video.get_publish_date()
        status = YoutubeVideo.STATUS_NO_STATUS
        video_type = YoutubeVideo.TYPE_REGULAR

        if not api_video.has_valid_duration():
            status = YoutubeVideo.STATUS_SKIP
            video_type = YoutubeVideo.TYPE_LONG

        video = YoutubeVideo(video_id, title, channel_name, published_at, self.video_count, self.save_location,
                             file_extension=self.file_extension, file_name=None, video_quality=self.video_quality,
                             video_type=video_type, status=status)
        return video

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        YoutubeWatcher.validate_data(data)

        name = data.get(WATCHER_NAME)
        channel_id = data.get(CHANNEL_ID)
        check_date = data.get(CHECK_DATE, datetime_utils.get_default_utc())
        video_count = data.get(VIDEO_COUNT, 0)
        file_extension: FileExtension = FileExtension.from_str(data.get(FILE_EXTENSION))
        playlist_file = data.get(PLAYLIST_FILE)
        download = data.get(DOWNLOAD)
        video_quality = data.get(VIDEO_QUALITY, None)

        obj = YoutubeWatcher(name, channel_id, check_date, video_count, file_extension,
                             download, playlist_file, video_quality)
        return obj

    @classmethod
    def from_file(cls, file_path: str) -> list[Self]:
        data = file.read_json(file_path)
        watchers = [YoutubeWatcher.from_dict(watcher_dict) for watcher_dict in data]
        return watchers

    def update_db(self):
        self.db_videos.add(self.videos)
        self.db_videos.write(self.db_file)

    def extract_missing(self) -> list[YoutubeVideo]:
        missing_videos = []
        for api_video in self.api_videos:
            if self.db_videos.get_by_id(api_video.get_id()) is None:
                video = self.init_video(api_video)
                video.number = self.db_videos.calculate_insert_number(video.published_at)
                video.file_name = video.generate_file_name()
                self.video_count += 1
                self.db_videos.insert(video)
                missing_videos.append(video)

        self.missing_videos = missing_videos
        return self.missing_videos

    def extract_changed(self) -> list[tuple[YoutubeVideo, YoutubeVideo]]:
        changed_videos = []
        for api_video in self.api_videos:
            db_video = self.db_videos.get_by_id(api_video.get_id())
            if db_video:
                video = self.init_video(api_video)
                if db_video.has_changed(video):
                    changed_videos.append((db_video, video))

        self.changed_videos = changed_videos
        return self.changed_videos

    def to_json(self) -> str:
        json_data = ""
        json_data += f" {{ "
        json_data += f"\"{WATCHER_NAME}\": \"{self.name}\", "
        json_data += f"\"{CHANNEL_ID}\": \"{self.channel_id}\", "
        json_data += f"\"{CHECK_DATE}\": \"{self.check_date}\", "
        json_data += f"\"{VIDEO_COUNT}\": {self.video_count}, "
        json_data += f"\"{FILE_EXTENSION}\": \"{self.file_extension.value}\", "
        json_data += f"\"{DOWNLOAD}\": {str(self.download).lower()}"
        if self.video_quality:
            json_data += f", \"{VIDEO_QUALITY}\": {self.video_quality}"
        if self.playlist_file:
            json_data += f", \"{PLAYLIST_FILE}\": \"{self.playlist_file}\""
        json_data += f" }}"

        return json_data

    def __repr__(self):
        return ";".join([self.name, self.channel_id, self.check_date, str(self.video_count), self.file_extension.value])
