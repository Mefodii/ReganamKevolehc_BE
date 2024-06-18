from enum import Enum

from constants import constants
from contenting.reganam_tnetnoc.model.file_extension import FileExtension

ARGUMENTS_FLAG = "<!>"
WATCHER_LIKE_FLAG = "<#>"
COMMENT_FLAG = "#"
SEPARATOR = ";"

DEFAULT_TITLE = '%(title)s'
DEFAULT_EXTENSION = FileExtension.MP3

POS_QUEUE_TYPE = 0
POS_TITLE = 1
POS_FILE_EXTENSION = 2
POS_VIDEO_QUALITY = 3
POS_URL = 4
POS_CHANNEL_NAME = 5
POS_TRACK_NR = 6

ARGS_TYPE_TOTAL_ARGS = 5
WATCHER_TYPE_TOTAL_ARGS = 7


class InputQueueType(Enum):
    DEFAULT = "default"
    ARGUMENTS = ARGUMENTS_FLAG
    WATCHER_LIKE = WATCHER_LIKE_FLAG


class InputQueue:
    def __init__(self, queue_type: InputQueueType, title: str, file_extension: FileExtension, url: str,
                 video_quality: int = None, channel_name: str = None, track_nr: int = None):
        self.queue_type = queue_type
        self.title = title
        self.file_extension = file_extension
        self.video_quality = video_quality
        self.url = url
        self.channel_name = channel_name
        self.track_nr = track_nr

    def get_video_id(self):
        return self.url[32:]

    @classmethod
    def from_str(cls, data: str):
        queue_type = InputQueueType.DEFAULT
        title = DEFAULT_TITLE
        file_extension = DEFAULT_EXTENSION
        video_quality = None
        track_nr = None
        channel_name = None
        url = data

        args = data.split(SEPARATOR)
        if args[POS_QUEUE_TYPE] in [ARGUMENTS_FLAG, WATCHER_LIKE_FLAG]:
            queue_type = InputQueueType(args[POS_QUEUE_TYPE])
            expected_args = ARGS_TYPE_TOTAL_ARGS if queue_type == InputQueueType.ARGUMENTS else WATCHER_TYPE_TOTAL_ARGS

            if len(args) != expected_args:
                raise Exception(f"Expected args: {expected_args}. Received: {len(args)}. Data: {data}")

            if len(args[POS_TITLE]) != 0:
                title = args[POS_TITLE]
            if len(args[POS_FILE_EXTENSION]) != 0:
                file_extension = FileExtension.from_str(args[POS_FILE_EXTENSION])
            if len(args[POS_VIDEO_QUALITY]) != 0:
                video_quality = int(args[POS_VIDEO_QUALITY])
            url = args[POS_URL]

            if queue_type == InputQueueType.WATCHER_LIKE:
                if len(args[POS_CHANNEL_NAME]) == 0:
                    raise Exception(f"Expected value for channel_name on position: {POS_CHANNEL_NAME}.")
                if len(args[POS_TRACK_NR]) == 0:
                    raise Exception(f"Expected value for track_nr on position: {POS_TRACK_NR}.")
                if not url.startswith(constants.DEFAULT_YOUTUBE_WATCH):
                    raise Exception(f"Expected url to be from Youtube. Received: {url}.")

                channel_name = args[POS_CHANNEL_NAME]
                track_nr = int(args[POS_TRACK_NR])

        if len(url) == 0:
            raise Exception("Url should not be empty")

        return cls(queue_type, title, file_extension, url, video_quality, channel_name, track_nr)
