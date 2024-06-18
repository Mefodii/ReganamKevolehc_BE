from utils.string_utils import normalize_file_name
from contenting.reganam_tnetnoc.model.file_extension import FileExtension
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo

INFO_DICT = "info_dict"


class YoutubeQueue:
    def __init__(self, video_id: str, file_name: str, save_location: str, file_extension: FileExtension,
                 video_quality: int = None, url: str = None, source: YoutubeVideo = None):
        self.video_id = video_id
        self.file_name = normalize_file_name(file_name)
        self.save_location = save_location
        self.file_extension = file_extension
        self.url = url
        self.video_quality = video_quality
        self.source = source

        self.audio_dl_stats = None
        self.video_dl_stats = None

    @classmethod
    def from_youtubevideo(cls, video: YoutubeVideo):
        obj = cls(video.video_id, video.file_name, video.save_location, video.file_extension,
                  video.video_quality, video.get_url(), source=video)
        return obj

    def get_file_abs_path(self):
        return f"{self.save_location}\\{self.file_name}.{self.file_extension.value}"

    def replace_file_name_tags(self):
        file_name = self.file_name
        for key, value in self.video_dl_stats.get(INFO_DICT).items():
            tag = f"%({key})s"
            if tag in file_name:
                file_name = file_name.replace(tag, value)
        if file_name != self.file_name:
            self.file_name = normalize_file_name(file_name)

    def __repr__(self):
        return ";".join([self.video_id, self.url, self.file_name, self.save_location, self.file_extension.value,
                         str(self.video_quality)])
