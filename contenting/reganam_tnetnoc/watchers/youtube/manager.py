from __future__ import unicode_literals, annotations

# noinspection PyProtectedMember
from yt_dlp import DownloadError

from constants import env
from constants.paths import WATCHERS_DOWNLOAD_PATH, FILES_AUDIO_ARCHIVE_PATH, \
    FILES_VIDEO_ARCHIVE_PATH
from contenting.reganam_tnetnoc.model.file_tags import FileTags
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItem, PlaylistItemList
from contenting.reganam_tnetnoc.utils import media_utils
from contenting.reganam_tnetnoc.utils.downloader import YoutubeDownloader
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from contenting.reganam_tnetnoc.watchers.youtube.queue import YoutubeQueue
from contenting.reganam_tnetnoc.watchers.youtube.watcher import YoutubeWatcher
from utils import file
from utils.datetime_utils import compare_yt_dates, utcnow, default_utc
from utils.ffmpeg import Ffmpeg


class YoutubeWatchersManager:
    """
    Manager for keeping YouTube channels up to date by using .json as input and .txt file as database
    """

    def __init__(self, api_worker: YoutubeWorker, watchers_file: str = None, log_file: str = None):
        self.log_file = log_file
        self.api = api_worker
        self.watchers_file = watchers_file
        self.watchers: list[YoutubeWatcher] = YoutubeWatcher.from_file(watchers_file) if watchers_file else []
        self.queue_list: list[YoutubeQueue] = []
        self.processed_queue_list: list[YoutubeQueue] = []
        self.downloader = YoutubeDownloader(env.FFMPEG)

    # Add message to the log file
    def log(self, message, console_print: bool = False) -> None:
        if self.log_file is None:
            print(message)
        else:
            file.append(self.log_file, message)
            if console_print:
                print(message)

    def run_updates(self) -> None:
        self.check_for_updates()
        self.generate_queue()
        self.download_queue()
        self.append_tags()
        self.update_files()
        self.finish()

    def run_integrity(self):
        self.log(str(utcnow()) + " - starting to check for missing videos", True)
        self.extract_all_api_videos()
        self.generate_queue()
        self.download_queue()
        self.append_tags()
        self.update_files_integrity()
        self.update_media_files()
        self.finish()

    def retry_unables(self):
        for watcher in self.watchers:
            videos_list = watcher.db_videos

            for db_video in videos_list.videos:
                if db_video.status == YoutubeVideo.STATUS_UNABLE:
                    db_video.status = YoutubeVideo.STATUS_NO_STATUS
                    db_video.save_location = watcher.save_location
                    db_video.video_quality = watcher.video_quality
                    watcher.append_video(db_video)

        self.generate_queue()
        self.download_queue()
        self.append_tags()
        self.update_files_unables()

    def simple_download(self, videos: list[YoutubeVideo]):
        dummy_watcher = YoutubeWatcher.dummy()
        dummy_watcher.videos = videos
        self.watchers.append(dummy_watcher)

        self.generate_queue()
        self.download_queue()
        self.append_tags()

    def check_for_updates(self) -> None:
        self.log(str(utcnow()) + " - starting update process for watchers")
        for watcher in self.watchers:
            self.log(f'Checking: {watcher.channel_id} - {watcher.name}', True)
            watcher.new_check_date = utcnow()
            api_videos = self.api.get_uploads(watcher.channel_id, watcher.check_date)

            self.log(f"{watcher.name.ljust(30)} || New uploads - {len(api_videos)}", True)
            for api_video in api_videos:
                self.log("\t" + repr(api_video))
                print(f"{api_video.get_publish_date()} | {api_video.get_id()} | {api_video.get_title()}")
                watcher.video_count += 1
                video = watcher.init_video(api_video)
                if video.status == YoutubeVideo.STATUS_SKIP:
                    self.log(f"Video skipped: {api_video.get_id()}", True)
                    print(f"Video data: {video}")
                    print(f"Api data: {api_video}")
                watcher.append_video(video)

    def extract_all_api_videos(self):
        for watcher in self.watchers:
            watcher.new_check_date = watcher.check_date
            api_videos = self.api.get_uploads(watcher.channel_id, default_utc(),
                                              watcher.check_date)
            watcher.api_videos = api_videos
            watcher.extract_missing()
            watcher.extract_changed()

    def generate_queue(self) -> None:
        self.log("Generating download queue")

        self.queue_list = []
        for watcher in self.watchers:
            if not watcher.download:
                continue

            for video in watcher.videos + watcher.missing_videos:
                if video.status != YoutubeVideo.STATUS_NO_STATUS:
                    continue

                queue = YoutubeQueue.from_youtubevideo(video)
                self.queue_list.append(queue)
                print(repr(queue))

    # noinspection DuplicatedCode
    def download_queue(self):
        q_len = str(len(self.queue_list))

        self.processed_queue_list = []
        for i, queue in enumerate(self.queue_list, start=1):
            queue: YoutubeQueue
            q_progress = f"{i}/{q_len}"

            result_file = queue.get_file_abs_path()
            if file.exists(result_file):
                self.log(f"Queue ignored, file exist: {q_progress}", True)
            else:
                self.log(f"Process queue: {q_progress} - {result_file}", True)
                try:
                    self.downloader.download(queue)
                except DownloadError:
                    self.log(f"Unable to download - {queue.url}", True)

            video = queue.source
            video.status = YoutubeVideo.STATUS_DOWNLOADED if file.exists(result_file) else YoutubeVideo.STATUS_UNABLE
            self.processed_queue_list.append(queue)
        self.queue_list = []

    def append_tags(self) -> None:
        for watcher in self.watchers:
            if not watcher.download:
                continue

            for video in watcher.videos + watcher.missing_videos:
                tags = FileTags.extract_from_youtubevideo(video)

                file_abs_path = video.get_file_abs_path()
                if file.exists(file_abs_path):
                    Ffmpeg.add_tags(file_abs_path, tags, loglevel="error")

    def update_files(self) -> None:
        for watcher in self.watchers:
            watcher.update_db()

            playlist_file = watcher.playlist_file
            if playlist_file:
                PlaylistItemList.append_videos(playlist_file, watcher.videos)

    def update_files_integrity(self):
        for watcher in self.watchers:
            self.log(f'Integrity log: {watcher.channel_id} - {watcher.name}', True)
            db_videos = watcher.db_videos
            playlist_file = watcher.playlist_file
            playlist_items = watcher.playlist_items

            for video in watcher.missing_videos:
                self.log(f"Missing video inserted at: {video.number}. Video: {video.to_dict()}", True)
                if playlist_file:
                    item = PlaylistItem.from_youtubevideo(video)
                    playlist_items.insert(item)

            for db_video, new_video in watcher.changed_videos:
                # Compare timestamp and move if changed
                if compare_yt_dates(db_video.published_at, new_video.published_at) != 0:
                    message = (f"Changed publish date: {db_video.video_id} | API: {new_video.published_at} | "
                               f"DB: {db_video.published_at}")
                    self.log(message, True)
                    db_video.published_at = new_video.published_at

                    new_number = db_videos.calculate_insert_number(db_video.published_at)
                    self.log(f"Moving from: {db_video.number} to: {new_number}", True)
                    db_videos.move(db_video, new_number)
                    if playlist_file:
                        item = PlaylistItem.from_youtubevideo(db_video)
                        playlist_items.move(item, new_number)

                # Check and update video title in db if changed
                if db_video.title != new_video.title:
                    message = (f"Changed title. Id: {db_video.video_id} | Nr: {db_video.number} | "
                               f"API: {new_video.title} | DB: {db_video.title}")
                    self.log(message, True)
                    db_video.title = new_video.title
                    db_video.file_name = db_video.generate_file_name()

            if watcher.missing_videos or watcher.changed_videos:
                db_videos.write(watcher.db_file)
                if playlist_file:
                    playlist_items.write(playlist_file)

    def update_files_unables(self):
        for watcher in self.watchers:
            playlist_file = watcher.playlist_file
            playlist_items = watcher.playlist_items

            updated = False
            for video in watcher.videos:
                if video.status == YoutubeVideo.STATUS_DOWNLOADED:
                    updated = True
                    if playlist_file:
                        item = playlist_items.get_by_url(video.get_url())
                        if item.item_flag == PlaylistItem.ITEM_FLAG_MISSING:
                            item.item_flag = PlaylistItem.ITEM_FLAG_DEFAULT

            if updated:
                watcher.db_videos.write(watcher.db_file)
                if watcher.playlist_file:
                    watcher.playlist_items.write(watcher.playlist_file)

    def update_media_files(self):
        for watcher in self.watchers:
            if not watcher.download:
                continue

            if not watcher.missing_videos and not watcher.changed_videos:
                continue

            media_paths = [
                WATCHERS_DOWNLOAD_PATH + "\\" + watcher.name,
                FILES_AUDIO_ARCHIVE_PATH + "\\" + watcher.name,
                FILES_VIDEO_ARCHIVE_PATH + "\\" + watcher.name
            ]
            media_paths = list(filter(lambda p: file.dir_exists(p), media_paths))
            media_utils.sync_media_filenames_with_db(watcher.db_file, media_paths, watcher.file_extension)

    def finish(self) -> None:
        for watcher in self.watchers:
            watcher.check_date = watcher.new_check_date

        watchers_json = ["[", ",\n".join([watcher.to_json() for watcher in self.watchers]), "]"]
        file.write(self.watchers_file, watchers_json, file.ENCODING_UTF8)
