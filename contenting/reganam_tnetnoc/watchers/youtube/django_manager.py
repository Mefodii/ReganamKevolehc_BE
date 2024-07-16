# noinspection PyProtectedMember
from yt_dlp import DownloadError

from constants import env, paths
from constants.enums import DownloadStatus, ContentItemType, ContentWatcherStatus
from constants.enums import FileExtension
from contenting.models import ContentWatcher, ContentItem, ContentMusicItem
from contenting.reganam_tnetnoc.model.file_tags import FileTags
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItemList
from contenting.reganam_tnetnoc.utils.downloader import YoutubeDownloader
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker, YoutubeAPIItem
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from contenting.reganam_tnetnoc.watchers.youtube.queue import YoutubeQueue
from contenting.reganam_tnetnoc.watchers.youtube.watcher import YoutubeWatcher
from utils import datetime_utils, file
from utils.ffmpeg import Ffmpeg
from utils.string_utils import normalize_file_name


# TODO: https://channels.readthedocs.io/en/stable/tutorial/part_1.html
# TODO: https://medium.com/@adabur/introduction-to-django-channels-and-websockets-cb38cd015e29
class YoutubeWatcherDjangoManager:
    """
    Manager for keeping YouTube channels up to date by using django models and database
    """

    def __init__(self, api_worker: YoutubeWorker, watcher: ContentWatcher, log_file: str = None):
        self.log_file = log_file
        self.api: YoutubeWorker = api_worker
        self.watcher: ContentWatcher = watcher

        self.downloader = YoutubeDownloader(env.FFMPEG)
        self.save_location: str = "\\".join([paths.WATCHERS_DOWNLOAD_PATH, self.watcher.name])

    def log(self, message, console_print: bool = False) -> None:
        if self.log_file is None:
            print(message)
        else:
            file.append(self.log_file, message)
            if console_print:
                print(message)

    def run_updates(self) -> None:
        if self.watcher.status in (ContentWatcherStatus.DEAD.value, ContentWatcherStatus.NONE.value,
                                   ContentWatcherStatus.IGNORE.value):
            return

        try:
            self.watcher.status = ContentWatcherStatus.RUNNING.value
            self.watcher.save()

            new_check_date = datetime_utils.utcnow()
            check_date = datetime_utils.py_to_yt(self.watcher.check_date)

            self.log(f'{new_check_date}. '
                     f'Checking: {self.watcher.watcher_id} - {self.watcher.name}', True)
            new_yt_uploads = self.api.get_uploads(self.watcher.watcher_id, check_date)
            self.log(f"{self.watcher.name.ljust(30)} || New uploads - {len(new_yt_uploads)}", True)

            new_content_items = self.process_new_uploads(new_yt_uploads)
            if self.watcher.download:
                self.download_pending(new_content_items)
                self.append_tags(new_content_items)

                self.temp_old_func(new_content_items)

            for content_item in new_content_items:
                content_item.save()
            self.watcher.check_date = new_check_date
            self.watcher.status = ContentWatcherStatus.FINISHED.value
            self.watcher.save()
        except Exception as e:
            self.watcher.status = ContentWatcherStatus.ERROR.value
            self.watcher.save()
            raise e

    def temp_old_func(self, new_content_items: list[ContentItem | ContentMusicItem]):
        # TODO: this is a temporary writing to the old playlist / db file. Just in case
        playlist_file = r"E:/Google Drive/Mu/plist/" + self.watcher.name + ".txt"
        old_watcher = YoutubeWatcher(self.watcher.name, self.watcher.watcher_id, "", -1,
                                     FileExtension.from_str(self.watcher.file_extension), True,
                                     playlist_file, self.watcher.video_quality)
        if self.watcher.is_music():
            PlaylistItemList.append_content_items(playlist_file, new_content_items)

        videos: list[YoutubeVideo] = []
        for item in new_content_items:
            video_id = item.item_id
            title = item.title
            channel_name = self.watcher.name
            published_at = datetime_utils.py_to_yt(item.published_at)
            number = item.position
            file_extension = old_watcher.file_extension
            file_name = item.file_name
            video_quality = None if self.watcher.video_quality == -1 else self.watcher.video_quality
            status = item.download_status
            video_type = YoutubeVideo.TYPE_REGULAR

            video = YoutubeVideo(video_id, title, channel_name, published_at, number, save_location=None,
                                 file_extension=file_extension, file_name=file_name, video_quality=video_quality,
                                 status=status, video_type=video_type)
            videos.append(video)

        old_watcher.videos = videos
        old_watcher.update_db()
        # TODO: read the watchers JSON file and update the watcher there is exists

    def run_integrity(self):
        # TODO: implement
        ...

    def retry_unables(self):
        # TODO: implement
        ...

    def process_new_uploads(self, new_yt_uploads: list[YoutubeAPIItem]) -> list[ContentItem | ContentMusicItem]:
        items_count = self.watcher.get_items_count()
        result: list[ContentItem | ContentMusicItem] = []
        ids_set = set()
        for api_video in new_yt_uploads:
            self.log("\t" + repr(api_video))
            print(f"{api_video.get_publish_date()} | {api_video.get_id()} | {api_video.get_title()}")

            items_count += 1
            if self.watcher.is_music():
                content_item = self.new_content_music_item(api_video, items_count)
            else:
                content_item = self.new_content_item(api_video, items_count)

            db_content_item = self.watcher.get_content_item(content_item.item_id)
            if db_content_item:
                raise ValueError(f"Content item with id: {db_content_item.item_id} already exists. "
                                 f"DB Item: {str(db_content_item)}")

            if content_item.item_id in ids_set:
                raise ValueError(f"Item {content_item.item_id} is already in list. Item: {str(content_item)}")
            else:
                ids_set.add(content_item.item_id)

            if content_item.download_status == DownloadStatus.SKIP.value:
                self.log(f"Video skipped: {api_video.get_id()}", True)
                print(f"Api data: {api_video}")

            result.append(content_item)

        return result

    def new_content_item(self, yt_api_item: YoutubeAPIItem, position: int) -> ContentItem:
        content_item = ContentItem()
        self.set_content_item_common_fields(content_item, yt_api_item, position)
        content_item.consumed = False
        return content_item

    def new_content_music_item(self, yt_api_item: YoutubeAPIItem, position: int) -> ContentMusicItem:
        content_item = ContentMusicItem()
        self.set_content_item_common_fields(content_item, yt_api_item, position)
        content_item.type = ContentItemType.UNKNOWN.value
        content_item.parsed = False
        return content_item

    def set_content_item_common_fields(self, content_item: ContentItem | ContentMusicItem, yt_api_item: YoutubeAPIItem,
                                       position: int) -> None:
        content_item.item_id = yt_api_item.get_id()
        content_item.url = yt_api_item.get_url()
        content_item.title = yt_api_item.get_title()
        content_item.file_name = ""
        content_item.position = position
        content_item.download_status = DownloadStatus.NONE.value
        content_item.published_at = datetime_utils.yt_to_py(yt_api_item.get_publish_date())
        content_item.content_list = self.watcher.content_list

        if self.watcher.download:
            content_item.file_name = normalize_file_name(
                " - ".join([str(position), self.watcher.name, content_item.title]))
            skip = not yt_api_item.has_valid_duration()
            content_item.download_status = DownloadStatus.SKIP.value if skip else DownloadStatus.PENDING.value

    # noinspection DuplicatedCode
    def download_pending(self, content_items: list[ContentItem | ContentMusicItem]):
        q_len = str(len(content_items))
        for i, content_item in enumerate(content_items, start=1):
            q_progress = f"{i}/{q_len}"

            if content_item.download_status != DownloadStatus.PENDING.value:
                self.log(f"Queue ignored, item status {content_item.download_status} / {q_progress}", True)
                continue

            queue = self.new_queue(content_item)
            result_file = queue.get_file_abs_path()

            if file.exists(result_file):
                self.log(f"Queue ignored, file exist: {q_progress}", True)
            else:
                self.log(f"Process queue: {q_progress} - {result_file}", True)
                try:
                    self.downloader.download(queue)
                except DownloadError:
                    self.log(f"Unable to download - {queue.url}", True)

            if file.exists(result_file):
                content_item.download_status = DownloadStatus.DOWNLOADED.value
            else:
                content_item.download_status = DownloadStatus.UNABLE.value

    def new_queue(self, content_item: ContentItem | ContentMusicItem) -> YoutubeQueue:
        queue = YoutubeQueue(
            video_id=content_item.item_id,
            file_name=content_item.file_name,
            save_location=self.save_location,
            file_extension=FileExtension.from_str(self.watcher.file_extension),
            video_quality=self.watcher.video_quality,
            url=content_item.url,
        )
        return queue

    def append_tags(self, content_items: list[ContentItem | ContentMusicItem]) -> None:
        for item in content_items:
            if item.download_status != DownloadStatus.DOWNLOADED.value:
                continue

            tags = FileTags.extract_from_content_item(self.watcher, item)

            file_abs_path = f"{self.save_location}\\{item.file_name}.{self.watcher.file_extension}"
            if file.exists(file_abs_path):
                Ffmpeg.add_tags(file_abs_path, tags, loglevel="error")
