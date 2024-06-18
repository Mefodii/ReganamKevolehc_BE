from __future__ import unicode_literals

import time

from constants import paths
from constants.paths import (WATCHERS_DOWNLOAD_PATH, FILES_AUDIO_ARCHIVE_PATH,
                             FILES_VIDEO_ARCHIVE_PATH, PLAYLIST_FILES_PATH)
from contenting.reganam_tnetnoc.utils import media_utils, playlist_utils, db_utils
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.manager import YoutubeWatchersManager
from utils import file
from utils.file import File

DB_TO_IGNORE = [
    "TheNetNinja.txt"
]


#
#
# # Read all monitors and cross-check with db files.
# # Add missing videos with "MISSING" status and Number = 0.
# def check_db_integrity():
#     monitors_db = paths.YOUTUBE_WATCHERS_PATH
#     monitors_db = paths.YOUTUBE_WATCHERS_PGM_PATH
#     monitors_db = paths.YOUTUBE_WATCHERS2_PATH
#     dk_file = paths.API_KEY_PATH
#
#     worker = YoutubeWorker(dk_file)
#     manager = MonitorManager(monitors_db, worker, paths.YOUTUBE_API_LOG)
#     for monitor in manager.monitors:
#         default_reference_date = yt_datetime.get_default_ytdate()
#         db_file = '\\'.join([paths.DB_LOG_PATH, monitor.name + ".txt"])
#         db_json = File.get_json_data(db_file)
#
#         prepare_videos(manager, monitor, default_reference_date)
#
#         for video in monitor.videos:
#             db_video = db_json.get(video.video_id, None)
#             # Check if video exists in db
#             if db_video is None:
#                 db_json[video.video_id] = {"STATUS": "MISSING", "TITLE": video.title,
#                                            "PUBLISHED_AT": video.published_at,
#                                            "FILE_NAME": video.file_name, "SAVE_LOCATION": video.save_location,
#                                            "NUMBER": video.number, "CHANNEL_NAME": video.channel_name,
#                                            "FORMAT": monitor.format}
#                 print(db_json[video.video_id])
#             else:
#                 # Add timestamp if missing
#                 if db_video.get(YoutubeVideo.PUBLISHED_AT, None) is None:
#                     db_json[video.video_id][YoutubeVideo.PUBLISHED_AT] = video.published_at
#
#                 # Compare timestamp
#                 if compare_yt_dates(db_video.get(YoutubeVideo.PUBLISHED_AT), video.published_at) != 0:
#                     print(str(db_video.get(YoutubeVideo.NUMBER)), "API: ", video.published_at, "DB: ",
#                           db_video.get(YoutubeVideo.PUBLISHED_AT), sep=" | ")
#                     db_json[video.video_id][YoutubeVideo.PUBLISHED_AT] = video.published_at
#
#                 # Check and update video title in db if changed
#                 if not db_video.get(YoutubeVideo.TITLE) == video.title:
#                     print(str(db_video.get(YoutubeVideo.NUMBER)), video.title, db_video.get(YoutubeVideo.TITLE),
#                           sep=" | ")
#                     db_json[video.video_id][YoutubeVideo.TITLE] = video.title
#
#         File.write_json_data(db_file, db_json)


def check_db_playlist_media_validity():
    def need_process(f: File) -> bool:
        return f.name not in DB_TO_IGNORE

    db_files = file.list_files(paths.WATCHER_JSON_DB_PATH)

    for db_file in db_files:
        db_file_path = db_file.get_abs_path()
        print(f"Checking: {db_file.name}")
        valid = db_utils.check_validity(db_file_path)
        print(f"DB Validity: {valid}")
        if not valid:
            continue

        to_process = need_process(db_file)
        playlist_file = f"{PLAYLIST_FILES_PATH}\\{db_file.name}"
        if file.exists(playlist_file) and to_process:
            valid = playlist_utils.check_validity(playlist_file, db_file_path)
            print(f"Playlist Validity: {valid}")
            if not valid:
                continue

        if to_process:
            file_name_no_ext = db_file.get_plain_name()
            media_paths = [
                WATCHERS_DOWNLOAD_PATH + "\\" + file_name_no_ext,
                FILES_AUDIO_ARCHIVE_PATH + "\\" + file_name_no_ext,
                FILES_VIDEO_ARCHIVE_PATH + "\\" + file_name_no_ext
            ]

            media_paths = list(filter(lambda p: file.dir_exists(p), media_paths))
            valid = media_utils.check_validity(db_file_path, media_paths)
            print(f"Media Validity: {valid}")


def run_watchers_integrity():
    youtube_watchers = paths.YOUTUBE_WATCHERS_PATH
    # youtube_watchers = paths.YOUTUBE_WATCHERS_PGM_PATH
    dk_file = paths.API_KEY_PATH

    worker = YoutubeWorker(dk_file)
    manager = YoutubeWatchersManager(worker, youtube_watchers, paths.YOUTUBE_API_LOG)
    manager.run_integrity()


def run_watchers_unables():
    youtube_watchers = paths.YOUTUBE_WATCHERS_PATH
    # youtube_watchers = paths.YOUTUBE_WATCHERS_PGM_PATH
    dk_file = paths.API_KEY_PATH

    worker = YoutubeWorker(dk_file)
    manager = YoutubeWatchersManager(worker, youtube_watchers, paths.YOUTUBE_API_LOG)
    manager.retry_unables()


#######################################################################################################################
# Main function
#######################################################################################################################
def __main__():
    # check_db_playlist_media_validity()
    run_watchers_integrity()
    # run_watchers_unables()
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
