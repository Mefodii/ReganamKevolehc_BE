from __future__ import unicode_literals, annotations

import time

from constants import paths
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.manager import YoutubeWatchersManager


#######################################################################################################################
# Main function
#######################################################################################################################
def __main__():
    watcher_files = [
        paths.YOUTUBE_WATCHERS_PATH,
        # paths.YOUTUBE_WATCHERS_PGM_PATH,
    ]

    dk_file = paths.API_KEY_PATH
    worker = YoutubeWorker(dk_file)
    for watcher_file in watcher_files:
        manager = YoutubeWatchersManager(worker, watcher_file, paths.YOUTUBE_API_LOG)
        manager.run_updates()


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
