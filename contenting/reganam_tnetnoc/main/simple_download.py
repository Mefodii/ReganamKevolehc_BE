from __future__ import unicode_literals

import os
import sys
import time
import traceback

from constants import env, paths
from contenting.reganam_tnetnoc.model.input_queue import InputQueue, InputQueueType, COMMENT_FLAG
from contenting.reganam_tnetnoc.settings.settings import YTDownloadSettings
from contenting.reganam_tnetnoc.utils.downloader import YoutubeDownloader
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.manager import YoutubeWatchersManager
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from contenting.reganam_tnetnoc.watchers.youtube.queue import YoutubeQueue
from utils import file

DEFAULT_SETTINGS = "settings.json"


def process_my_location():
    abs_path = repr(sys.argv[0])[1:-1]

    split_by = "/"
    if "\\" in abs_path:
        split_by = "\\"

    return "\\".join(abs_path.split(split_by)[0:-1])


MY_LOCATION = process_my_location()


def print_traceback():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
    traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=2, file=sys.stdout)
    traceback.print_exc()
    formatted_lines = traceback.format_exc().splitlines()
    print(formatted_lines[0])
    print(formatted_lines[-1])
    print(repr(traceback.format_exception(exc_type, exc_value,
                                          exc_traceback)))
    print(repr(traceback.extract_tb(exc_traceback)))
    print(repr(traceback.format_tb(exc_traceback)))


def download_watcher_like(input_queue: list[InputQueue], save_location: str):
    # name = "CriticalRole" https://criticalrole.fandom.com/wiki/List_of_episodes
    data = {item.get_video_id(): item for item in input_queue}

    api_worker = YoutubeWorker(paths.API_KEY_PATH)
    api_videos = api_worker.get_videos(list(data.keys()))

    videos = []
    for api_video in api_videos:
        video_id = api_video.get_id()
        input_queue_item: InputQueue = data.get(video_id)
        video = YoutubeVideo(video_id, api_video.get_title(), input_queue_item.channel_name,
                             api_video.get_publish_date(), input_queue_item.track_nr, save_location,
                             input_queue_item.file_extension, file_name=None,
                             video_quality=input_queue_item.video_quality)
        videos.append(video)

    manager = YoutubeWatchersManager(api_worker)
    manager.simple_download(videos)


#######################################################################################################################
# Main function
#######################################################################################################################
def __main__(settings_file):
    os.chdir(MY_LOCATION)
    print("Started at: " + MY_LOCATION)
    print("Settings: " + str(settings_file))
    if settings_file:
        settings = YTDownloadSettings(settings_file)

        input_file = '/'.join([MY_LOCATION, settings.input_file])
        output_directory = '/'.join([MY_LOCATION, settings.output_directory])
        resources_path = '/'.join([MY_LOCATION, settings.resources_path])
    else:
        input_file = '/'.join([paths.INPUT_FILES_PATH, paths.YOUTUBE_INPUT_FILE])
        output_directory = paths.YOUTUBE_RESULT_PATH
        resources_path = env.FFMPEG

    downloader = YoutubeDownloader(resources_path)

    input_lines = file.read(input_file, file.ENCODING_UTF8)
    input_lines = list(filter(lambda line: not line.startswith(COMMENT_FLAG), input_lines))
    input_queue = [InputQueue.from_str(line) for line in input_lines]
    simple_queue: list[InputQueue] = list(filter(lambda item: item.queue_type == InputQueueType.ARGUMENTS, input_queue))
    simple_queue += list(filter(lambda item: item.queue_type == InputQueueType.DEFAULT, input_queue))
    watcher_type_queue: list[InputQueue] = list(filter(lambda item: item.queue_type == InputQueueType.WATCHER_LIKE,
                                                       input_queue))

    total_to_download = len(simple_queue)
    for i, j in enumerate(simple_queue):
        queue_item: InputQueue = j
        print("".join(["Downloading ", str(i + 1), "/", str(total_to_download)]))

        queue = YoutubeQueue("", queue_item.title, output_directory, queue_item.file_extension,
                             video_quality=queue_item.video_quality, url=queue_item.url)
        downloader.download(queue)

    if len(watcher_type_queue) > 0:
        download_watcher_like(watcher_type_queue, output_directory)


#######################################################################################################################
# Process
#######################################################################################################################
if __name__ == "__main__":
    # Start time of the program
    start = time.time()

    # Main functionality
    try:
        args = sys.argv

        if len(args) > 1:
            if args[1] == "local":
                __main__(None)
            else:
                print("Argument not valid")
        else:
            __main__(None)
    except:
        print_traceback()
        input("Press enter to end")
        raise

    # End time of the program
    end = time.time()
    # Running time of the program
    print("Program ran for: ", end - start, "seconds.")
