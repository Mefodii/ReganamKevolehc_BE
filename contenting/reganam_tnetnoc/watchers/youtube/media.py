from typing import Self

from unicodedata import normalize

from constants.constants import DEFAULT_YOUTUBE_WATCH
from constants.enums import FileExtension
from utils import file
from utils.datetime_utils import compare_yt_dates
from utils.string_utils import replace_unicode_chars, normalize_file_name


class YoutubeVideo:
    VIDEO_ID = "VIDEO_ID"
    TITLE = "TITLE"
    PUBLISHED_AT = "PUBLISHED_AT"
    CHANNEL_NAME = "CHANNEL_NAME"
    NUMBER = "NUMBER"
    FILE_NAME = "FILE_NAME"
    SAVE_LOCATION = "SAVE_LOCATION"
    STATUS = "STATUS"
    FILE_EXTENSION = "FILE_EXTENSION"
    VIDEO_QUALITY = "VIDEO_QUALITY"
    VIDEO_TYPE = "VIDEO_TYPE"

    STATUS_NO_STATUS = "NO_STATUS"
    STATUS_UNABLE = "UNABLE"
    STATUS_DOWNLOADED = "DOWNLOADED"
    STATUS_MISSING = "MISSING"
    STATUS_SKIP = "SKIP"

    TYPE_REGULAR = "TYPE_REGULAR"
    TYPE_SHORT = "TYPE_SHORT"
    TYPE_LIVESTREAM = "TYPE_LIVESTREAM"
    TYPE_LONG = "TYPE_LONG"

    def __init__(self, video_id: str, title: str, channel_name: str, published_at: str, number: int,
                 save_location: str = None, file_extension: FileExtension = None, file_name: str = None,
                 video_quality: int = None, video_type: str = None, status: str = None):
        self.video_id = video_id
        self.title = replace_unicode_chars(normalize('NFC', title))
        self.channel_name = channel_name
        self.published_at = published_at
        self.number = number
        self.save_location = save_location

        self.file_name = file_name
        self.init_file_name()
        self.file_extension = file_extension
        self.video_quality = video_quality

        self.video_type = video_type if video_type else self.TYPE_REGULAR
        self.status = status if status else YoutubeVideo.STATUS_NO_STATUS

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        video_id = data[YoutubeVideo.VIDEO_ID]
        title = data[YoutubeVideo.TITLE]
        channel_name = data[YoutubeVideo.CHANNEL_NAME]
        published_at = data[YoutubeVideo.PUBLISHED_AT]
        number = data[YoutubeVideo.NUMBER]
        file_extension = FileExtension.from_str(data[YoutubeVideo.FILE_EXTENSION])
        file_name = data[YoutubeVideo.FILE_NAME]
        video_quality = data.get(YoutubeVideo.VIDEO_QUALITY, None)
        status = data[YoutubeVideo.STATUS]
        video_type = data[YoutubeVideo.VIDEO_TYPE]

        obj = cls(video_id, title, channel_name, published_at, number, save_location=None,
                  file_extension=file_extension, file_name=file_name, video_quality=video_quality,
                  status=status, video_type=video_type)
        return obj

    def init_file_name(self) -> None:
        file_name = self.file_name
        if not file_name:
            file_name = self.generate_file_name()

        self.file_name = normalize_file_name(file_name)

    def generate_file_name(self) -> str:
        file_name = " - ".join([str(self.number), str(self.channel_name), str(self.title)])
        return normalize_file_name(file_name)

    def get_file_abs_path(self) -> str:
        return f"{self.save_location}\\{self.file_name}.{self.file_extension.value}"

    def get_url(self):
        return DEFAULT_YOUTUBE_WATCH + self.video_id

    def has_changed(self, other_video: Self) -> bool:
        if self.video_id != other_video.video_id:
            raise Exception(f"Unable to check changes on videos with different id. "
                            f"This ID: {self.video_id}. Other: {other_video.video_id}")

        return compare_yt_dates(self.published_at, other_video.published_at) != 0 or self.title != other_video.title

    def to_dict(self):
        data = {
            YoutubeVideo.VIDEO_ID: self.video_id,
            YoutubeVideo.TITLE: self.title,
            YoutubeVideo.CHANNEL_NAME: self.channel_name,
            YoutubeVideo.PUBLISHED_AT: self.published_at,
            YoutubeVideo.NUMBER: self.number,
            YoutubeVideo.FILE_EXTENSION: self.file_extension.value,
            YoutubeVideo.FILE_NAME: self.file_name,
            YoutubeVideo.VIDEO_QUALITY: self.video_quality,
            YoutubeVideo.STATUS: self.status,
            YoutubeVideo.VIDEO_TYPE: self.video_type,
        }

        # Remove all keys with value None
        data = {k: v for k, v in data.items() if v is not None}
        return data

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return str(self)


class YoutubeVideoList:

    def __init__(self, data: list[YoutubeVideo]):
        self.videos = data

    def add(self, videos: YoutubeVideo | list[YoutubeVideo]):
        items = [videos] if isinstance(videos, YoutubeVideo) else videos

        for video in items:
            if v := self.get_by_id(video.video_id):
                print(f"Warning!! Video with this ID already exists. Id: {v.video_id}. Number: {v.number}")
                print(f"Overwritting!! Old video: {v}. New video: {video}")

            self.videos.append(video)

    @classmethod
    def from_file(cls, file_path: str, empty_if_not_found: bool = False) -> Self:
        if not file.exists(file_path):
            if empty_if_not_found:
                return cls([])
            raise Exception(f"File not found: {file_path}")

        data = file.read_json(file_path)
        return cls([YoutubeVideo.from_dict(v) for v in data])

    def write(self, file_path: str, forced: bool = False) -> None:
        sort_ok = self.is_sorted()
        if not sort_ok and not forced:
            raise Exception(f"Write error: YoutubeVideoList not sorted. File: {file_path}.")

        if sort_ok:
            data = [v.to_dict() for v in self.videos]
        else:
            data = [v.to_dict() for v in self.get_sorted()]

        file.write_json(file_path, data)

    def move(self, video: YoutubeVideo, new_number: int):
        if video.number == new_number:
            print(f"Video already has this number. Move canceleld. Video id: {video.video_id}. Number: {new_number}")
            return

        self.delete(video)
        video.number = new_number
        video.file_name = video.generate_file_name()
        self.insert(video)

    def insert(self, video: YoutubeVideo) -> None:
        """
        Shift up by 1 all videos with number higher than current video, then insert given video
        :param video:
        :return:
        """
        if self.get_by_id(video.video_id):
            raise Exception(f"Video already exists. ID: {video.video_id}")
        expected_number = self.calculate_insert_number(video.published_at)

        if video.number == -1:
            video.number = expected_number
            video.file_name = video.generate_file_name()

        self.shift_number(position_start=video.number, position_end=None, step=1)
        self.videos.insert(video.number - 1, video)

    def delete(self, video: YoutubeVideo):
        """
        Remove video, then all videos after removed item are shifted down by 1.
        :param video:
        :return:
        """
        if video not in self.videos:
            raise Exception(f"Video not found. ID: {video.video_id}")

        self.videos.remove(video)
        self.shift_number(position_start=video.number, position_end=None, step=-1)

    def shift_number(self, position_start: int, position_end: int = None, step: int = 1):
        """
        All items within range position_start <= item.number <= position_end will have its number changed by step.

        Items are mutated with new position number and file_name
        :param position_start:
        :param position_end:
        :param step:
        :return:
        """
        for video in self.videos:
            if position_start <= video.number <= (position_end or float('inf')):
                video.number += step
                if video.number <= 0:
                    raise Exception(f"Number <= 0 not allowed. Video ID: {video.video_id}")

                video.file_name = video.generate_file_name()

    def calculate_insert_number(self, published_at: str) -> int:
        """
        Calculate video number based on published_at value
        :param published_at:
        :return:
        """
        videos_list = self.get_sorted()
        for video in videos_list:
            if compare_yt_dates(video.published_at, published_at) == 1:
                return video.number

        return videos_list[-1].number + 1

    def get_by_id(self, video_id: str) -> YoutubeVideo | None:
        for video in self.videos:
            if video.video_id == video_id:
                return video
        return None

    def get_sorted(self) -> list[YoutubeVideo]:
        """
        :return: videos sorted by number
        """
        return list(sorted(self.videos, key=lambda v: v.number))

    def is_sorted(self) -> bool:
        """
        Check that videos are sorted by number. Start from 1, no breaks.
        :return:
        """
        for i, video in enumerate(self.videos, start=1):
            video: YoutubeVideo
            if i != video.number:
                return False

        return True
