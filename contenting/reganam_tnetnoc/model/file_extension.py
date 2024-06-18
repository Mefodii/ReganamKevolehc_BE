from enum import Enum


class FileExtension(Enum):
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
