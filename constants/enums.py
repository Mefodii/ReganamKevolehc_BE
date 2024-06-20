from enum import Enum
from typing import Callable


# ######
# NOTE: These choices are mirrored in FE.
# Make sure when updating here, to also make the change in FE project as well
# ######


class EnumChoices(Enum):
    @classmethod
    def as_choices(cls, name_transformer: Callable[[str], str] = lambda v: v,
                   value_transformer: Callable[[str], str] = lambda v: v):
        return ((name_transformer(o.value), value_transformer(o.value)) for o in cls)


class ContentCategory(EnumChoices):
    MUSIC = "Music"
    FUN = "Fun"
    GAME = "Game"
    TECH = "Tech"
    OTHER = "Other"


class DownloadStatus(EnumChoices):
    NONE = "NONE"
    PENDING = "PENDING"
    DOWNLOADING = "DOWNLOADING"
    DOWNLOADED = "DOWNLOADED"
    UNABLE = "UNABLE"
    MISSING = "MISSING"
    SKIP = "SKIP"


class ContentItemType(EnumChoices):
    SINGLE = "Single"
    PLAYLIST = "Playlist"
    NOT_MUSIC = "NotMusic"


class ContentWatcherSourceType(EnumChoices):
    YOUTUBE = "Youtube"
    BANDCAMP = "Bandcamp"
    OTHER = "Other"


class FileExtension(EnumChoices):
    MKV = "mkv"
    MP4 = "mp4"
    MP3 = "mp3"
    M4A = "m4a"

    @classmethod
    def from_str(cls, value: str):
        return FileExtension(value.lower())

    def is_audio(self):
        return self in AUDIO_EXTENSIONS

    def is_video(self):
        return self in VIDEO_EXTENSIONS


AUDIO_EXTENSIONS = [FileExtension.MP3]
VIDEO_EXTENSIONS = [FileExtension.MP4, FileExtension.MKV]


class ContentWatcherStatus(EnumChoices):
    WAITING = "Waiting"
    RUNNING = "Running"
    FINISHED = "Finished"
    WARNING = "Warning"
    ERROR = "Error"
    DEAD = "Dead"
    NONE = "None"


class VideoQuality(EnumChoices):
    DEFAULT = -1
    Q720 = 720
    Q10080 = 1080


class WatchingType(EnumChoices):
    ANIME = "Anime"
    MOVIE = "Movie"
    SERIAL = "Serial"


class WatchingStatus(EnumChoices):
    DROPPED = "Dropped"
    PLANNED = "Planned"
    IGNORED = "Ignored"
    PREMIERE = "Premiere"
    WATCHING = "Watching"
    FINISHED = "Finished"


class WatchingAirStatus(EnumChoices):
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    UNKNOWN = "Unknown"
