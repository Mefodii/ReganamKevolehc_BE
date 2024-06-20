# noinspection PyProtectedMember
from yt_dlp import DownloadError

from constants import env, paths
from constants.enums import DownloadStatus, ContentItemType, ContentWatcherStatus
from constants.enums import FileExtension
from contenting.models import ContentWatcher, ContentItem, ContentMusicItem
from contenting.reganam_tnetnoc.utils.downloader import YoutubeDownloader
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker, YoutubeAPIItem
from contenting.reganam_tnetnoc.watchers.youtube.queue import YoutubeQueue
from utils import datetime_utils, file
from utils.string_utils import normalize_file_name


# TODO: https://channels.readthedocs.io/en/stable/tutorial/part_1.html
# TODO: https://medium.com/@adabur/introduction-to-django-channels-and-websockets-cb38cd015e29
class YoutubeWatcherDjangoManager:
    """
    Manager for keeping YouTube channels up to date by using django models and database
    """

    STATUS_OK = "OK"
    STATUS_WARNING = "WARNING"
    STATUS_ERROR = "ERROR"

    def __init__(self, api_worker: YoutubeWorker, watcher: ContentWatcher, log_file: str = None):
        self.log_file = log_file
        self.api: YoutubeWorker = api_worker
        self.watcher: ContentWatcher = watcher
        self.content_items = watcher.get_content_items()
        self.content_music_items = watcher.get_content_music_items()

        self.pending_content_items: list[ContentItem | ContentMusicItem] = []

        self.downloader = YoutubeDownloader(env.FFMPEG)
        self.new_check_date: str = ""
        self.status = YoutubeWatcherDjangoManager.STATUS_OK
        self.save_location: str = "\\".join([paths.WATCHERS_DOWNLOAD_PATH, self.watcher.name])

    def log(self, message, console_print: bool = False) -> None:
        if self.log_file is None:
            print(message)
        else:
            file.append(self.log_file, message)
            if console_print:
                print(message)

    def run_updates(self) -> None:
        if self.watcher.status in (ContentWatcherStatus.DEAD.value, ContentWatcherStatus.NONE.value):
            raise ValueError(f"Invalid status for watcher: {str(self.watcher)}")

        try:
            self.watcher.status = ContentWatcherStatus.RUNNING.value
            self.watcher.save()
            self.check_for_updates()
            self.download_pending()
            self.append_tags()

            if self.status == YoutubeWatcherDjangoManager.STATUS_OK:
                self.watcher.status = ContentWatcherStatus.FINISHED.value
            elif self.status == YoutubeWatcherDjangoManager.STATUS_WARNING:
                self.watcher.status = ContentWatcherStatus.WARNING.value
            elif self.status == YoutubeWatcherDjangoManager.STATUS_ERROR:
                self.watcher.status = ContentWatcherStatus.ERROR.value
            self.watcher.check_date = self.new_check_date
            self.watcher.save()
        except Exception as e:
            self.watcher.status = ContentWatcherStatus.ERROR.value
            self.watcher.save()
            raise e

    def run_integrity(self):
        # TODO: implement
        ...

    def retry_unables(self):
        # TODO: implement
        ...

    def check_for_updates(self) -> None:
        self.log(f'{str(datetime_utils.utcnow())}. '
                 f'Checking: {self.watcher.watcher_id} - {self.watcher.name}', True)

        check_date = datetime_utils.py_to_yt(self.watcher.check_date)
        self.new_check_date = datetime_utils.utcnow()
        api_videos = self.api.get_uploads(self.watcher.watcher_id, check_date)

        self.log(f"{self.watcher.name.ljust(30)} || New uploads - {len(api_videos)}", True)
        items_count = self.watcher.get_items_count()

        for api_video in api_videos:
            self.log("\t" + repr(api_video))
            print(f"{api_video.get_publish_date()} | {api_video.get_id()} | {api_video.get_title()}")
            items_count += 1
            if self.watcher.is_music():
                content_item = self.new_content_music_item(api_video, items_count)
            else:
                content_item = self.new_content_item(api_video, items_count)

            content_item.save()

            if content_item.download_status == DownloadStatus.SKIP.value:
                self.log(f"Video skipped: {api_video.get_id()}", True)
                print(f"Api data: {api_video}")

            if content_item.download_status == DownloadStatus.PENDING.value:
                self.pending_content_items.append(content_item)

    def new_content_item(self, yt_api_item: YoutubeAPIItem, position: int) -> ContentItem:
        content_item = ContentItem()
        self.set_content_item_common_fields(content_item, yt_api_item, position)
        content_item.consumed = False
        return content_item

    def new_content_music_item(self, yt_api_item: YoutubeAPIItem, position: int) -> ContentMusicItem:
        content_item = ContentMusicItem()
        self.set_content_item_common_fields(content_item, yt_api_item, position)
        content_item.type = ContentItemType.SINGLE.value
        return content_item

    def set_content_item_common_fields(self, content_item: ContentItem | ContentMusicItem, yt_api_item: YoutubeAPIItem,
                                       position: int) -> None:
        content_item.item_id = yt_api_item.get_id()
        content_item.url = yt_api_item.get_url()
        content_item.title = yt_api_item.get_title()
        content_item.file_name = None
        content_item.position = position
        content_item.download_status = DownloadStatus.NONE.value
        content_item.published_at = datetime_utils.yt_to_py(yt_api_item.get_publish_date())
        content_item.content_list = self.watcher.content_list

        if self.watcher.download:
            content_item.file_name = normalize_file_name(
                " - ".join([str(position), self.watcher.name, content_item.title]))
            skip = not yt_api_item.has_valid_duration()
            content_item.download_status = DownloadStatus.SKIP.value if skip else DownloadStatus.PENDING.value

    def download_pending(self):
        q_len = str(len(self.pending_content_items))
        for i, content_item in enumerate(self.pending_content_items, start=1):
            queue = self.new_queue(content_item)

            result_file = queue.get_file_abs_path()
            q_progress = f"{i}/{q_len}"
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
            content_item.save()

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

    def append_tags(self) -> None:
        # TODO: implement
        ...
