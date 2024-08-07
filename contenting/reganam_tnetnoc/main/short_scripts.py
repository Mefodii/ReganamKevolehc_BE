from __future__ import unicode_literals

import time

import yt_dlp as youtube_dl

from constants import paths, constants
from constants.enums import FileExtension
from constants.paths import WATCHERS_DOWNLOAD_PATH, FILES_VIDEO_ARCHIVE_PATH, FILES_AUDIO_ARCHIVE_PATH
from contenting.reganam_tnetnoc.utils import db_utils, playlist_utils, media_utils
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo, YoutubeVideoList
from utils import file
from utils.datetime_utils import yt_date_diff
from utils.string_utils import replace_chars_variations


def alter_db_kv():
    files = file.list_files(paths.WATCHER_JSON_DB_PATH)

    for item in files:
        db_file = item.get_abs_path()
        print(db_file)

        # videos_list = YoutubeVideoList.from_file(db_file)

        # change DB keys and values

        # videos_list.write(db_file)


def update_channel_kv():
    items = [
        ("AmbientMusicalGenre", "Ambient"),
    ]
    for old_name, new_name in items:
        old_db_file = f"{paths.WATCHER_JSON_DB_PATH}\\{old_name}.txt"
        new_db_file = f"{paths.WATCHER_JSON_DB_PATH}\\{new_name}.txt"

        print(old_db_file, new_db_file)
        if old_name != new_name:
            print(f"To rename: {old_name} to {new_name}")

        videos_list = YoutubeVideoList.from_file(old_db_file)

        for video in videos_list.videos:
            video.channel_name = new_name
            video.file_name = video.generate_file_name()

        videos_list.write(new_db_file)


def get_yt_video_info():
    dk_file = paths.API_KEY_PATH
    worker = YoutubeWorker(dk_file)
    video_ids = ["4ofJpOEXrZs"]
    print(worker.get_videos(video_ids))


def shift_db():
    db_file = r"E:\Tnetnoc\_db\Stradarium.txt"
    video_id = "DELETEME"

    video_id = "_Aszm-r0F-s"
    title = "Елена Осокина – Ленинград – Вашингтон: Сталинские продажи шедевров Эрмитажа"
    channel_name = "Stradarium"
    published_at = "2023-03-08T11:01:37Z"
    number = 7
    file_extension = FileExtension.MKV
    file_name = "7 - Stradarium - Елена Осокина – Ленинград – Вашингтон_ Сталинские продажи шедевров Эрмитажа"
    video_quality = None
    status = "DOWNLOADED"
    video_type = YoutubeVideo.TYPE_REGULAR

    video = YoutubeVideo(video_id, title, channel_name, published_at, number, save_location=None,
                         file_extension=file_extension, file_name=file_name, video_quality=video_quality,
                         status=status, video_type=video_type)
    db_utils.insert(db_file, [video])
    # db_utils.shift(db_file, 7, 1)
    # db_utils.delete(db_file, [video_id])


def shift_playlist():
    playlist_file = "E:\\Google Drive\\Mu\\plist\\GameChops.txt"
    video_url = constants.DEFAULT_YOUTUBE_WATCH + "ulARBhWUpA8"
    # playlist_utils.move_video_number(playlist_file, video_url, 367)
    playlist_utils.shift(playlist_file, 1289, -1)
    # playlist_utils.delete(playlist_file, [video_url])


def sync_media():
    watcher_name = "Stradarium"
    ext = FileExtension.MKV
    db_file = r"E:\Tnetnoc\_db\Stradarium.txt"
    media_paths = [
        WATCHERS_DOWNLOAD_PATH + "\\" + watcher_name,
        FILES_AUDIO_ARCHIVE_PATH + "\\" + watcher_name,
        FILES_VIDEO_ARCHIVE_PATH + "\\" + watcher_name
    ]
    media_paths = list(filter(lambda p: file.dir_exists(p), media_paths))
    media_utils.sync_media_filenames_with_db(db_file, media_paths, ext)


def db_to_list():
    for db_file in file.list_files("E:\\Coding\\Projects\\Kevolehc\\Kevolehc\\youtube\\files\\tests\\test_sync_media"):
        db_file_path = db_file.get_abs_path()
        db_data = file.read_json(db_file_path)

        videos = [YoutubeVideo.from_dict(v) for v in db_data.values()]
        videos = sorted(videos, key=lambda video: video.number)

        db_data = [v.to_dict() for v in videos]
        file.write_json(db_file_path, db_data)


def get_channel_id():
    dk_file = paths.API_KEY_PATH
    worker = YoutubeWorker(dk_file)
    video_id = "https://www.youtube.com/watch?v=pp091dH-8RA"
    video_id = video_id.replace("https://www.youtube.com/watch?v=", "")
    print(worker.get_channel_id_from_video(video_id))


def test_replace():
    texts = [
        "Voda-i-Ryba - Don`t Hesitate Don`t Panic",
        "A''laskan Tapes - No```w We’re Awake (And Everything Is Okay)",
        "BØJET - feelin’ high",
        "Nob–u Loops ‒ takara silva 88’",
        "Nobu Loops — takara silva 88````''",
        "Nobu Loops – takara silva 88’",
    ]

    for text in texts:
        after = replace_chars_variations(text)
        print(text == after, text, after)


def ytdl_get_info():
    url = "https://www.youtube.com/watch?v=4ofJpOEXrZs"
    with youtube_dl.YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)
        print(result)


def test_date_diff():
    diff = yt_date_diff("2024-02-21T03:22:22Z", "2024-02-21T03:22:22Z")
    print(diff)
    print(divmod(diff.total_seconds(), 3600)[0])
    print(divmod(diff.total_seconds(), 3600)[0] > 23.01)


#######################################################################################################################
# Main function
#######################################################################################################################
def __main__():
    # shift_db()
    # get_channel_id()
    # sync_media()
    # get_yt_video_info()
    # ytdl_get_info()
    # test_date_diff()
    pass


#######################################################################################################################
# Process
#######################################################################################################################
if __name__ == "__main__":
    # Start time of the program
    start = time.time()

    # Main functionality
    __main__()

    # End time of the program
    end = time.time()
    # Running time of the program
    print("Program ran for: ", end - start, "seconds.")
