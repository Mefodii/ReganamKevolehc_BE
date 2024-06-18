from __future__ import unicode_literals

import os
import time

from icecream import ic

from constants import paths
from constants.paths import TESTS_PATH
from contenting.reganam_tnetnoc.model.file_extension import FileExtension
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItem, PlaylistItemList
from contenting.reganam_tnetnoc.utils import playlist_utils, db_utils, media_utils
from contenting.reganam_tnetnoc.utils.ffmpeg import Ffmpeg
from contenting.reganam_tnetnoc.utils.yt_datetime import yt_to_py, compare_yt_dates
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo, YoutubeVideoList
from contenting.reganam_tnetnoc.watchers.youtube.watcher import YoutubeWatcher
from utils import file
from utils.file import File

TEST_READ_WRITE_PLAYLIST = "\\".join([TESTS_PATH, "test_read_write_playlist.txt"])
TEST_ADD_PLAYLIST_TRACKS = "\\".join([TESTS_PATH, "test_add_playlist_tracks.txt"])
TEST_ADD_PLAYLIST_TRACKS_DB = "\\".join([TESTS_PATH, "test_add_playlist_tracks_db.txt"])
TEST_ADD_PLAYLIST_TRACKS_RES = "\\".join([TESTS_PATH, "test_add_playlist_tracks_res.txt"])
TEST_PLAYLIST_SHIFT = "\\".join([TESTS_PATH, "test_playlist_shift.txt"])
TEST_PLAYLIST_DEL = "\\".join([TESTS_PATH, "test_playlist_del.txt"])
TEST_PLAYLIST_INSERT = "\\".join([TESTS_PATH, "test_playlist_insert.txt"])
TEST_PLAYLIST_MOVE = "\\".join([TESTS_PATH, "test_playlist_move.txt"])

TEST_READ_WRITE_DB = "\\".join([TESTS_PATH, "test_read_write_db.txt"])
TEST_DB_SHIFT = "\\".join([TESTS_PATH, "test_db_shift.txt"])
TEST_DB_DEL = "\\".join([TESTS_PATH, "test_db_del.txt"])
TEST_DB_INSERT = "\\".join([TESTS_PATH, "test_db_insert.txt"])
TEST_DB_MOVE = "\\".join([TESTS_PATH, "test_db_move.txt"])

TEST_WATCHERS = "\\".join([TESTS_PATH, "test_watchers.txt"])

TEST_SYNC_DB_PATH = "\\".join([TESTS_PATH, "test_sync_media"])
TEST_SYNC_DB_FILE = "\\".join([TEST_SYNC_DB_PATH, "db.txt"])
TEST_SYNC_DB_PATH_BEFORE = "\\".join([TEST_SYNC_DB_PATH, "before"])
TEST_SYNC_DB_PATH_AFTER = "\\".join([TEST_SYNC_DB_PATH, "after"])


def files_content_equal(f1, f2) -> bool:
    """
    read and compare the content of 2 files
    :param f1:
    :param f2:
    :return:
    """
    f1_data = file.read(f1, encoding=file.ENCODING_UTF8)
    f2_data = file.read(f2, encoding=file.ENCODING_UTF8)

    if len(f1_data) != len(f2_data):
        ic(f"Files length not equal. F1: {f1}. F2: {f2}")
        return False

    for i in range(len(f1_data)):
        if f1_data[i] != f2_data[i]:
            ic(f"Lines not equal. Line: {i + 1}. F1: {f1}. F2: {f2}")
            return False

    return True


def test_yt_to_py() -> bool:
    a = yt_to_py("2019-06-04T06:16:06.816Z")
    b = yt_to_py("2019-06-04T06:16:06.816Z")
    c = yt_to_py("2019-06-04T06:16:06.817Z")
    d = yt_to_py("2019-06-04T06:16:06.815Z")
    f = yt_to_py("2019-06-04T06:15:06.816Z")

    ok = True
    if not a == b:
        ic(f"Expected a == b. a: {a}. b: {b}")
        ok = False
    if not a < c:
        ic(f"Expected a < b. a: {a}. c: {b}")
        ok = False
    if not a > d:
        ic(f"Expected a > d. a: {a}. d: {b}")
        ok = False
    if not a > f:
        ic(f"Expected a > f. a: {a}. f: {f}")
        ok = False

    return ok


def test_video_sort_order() -> bool:
    dk_file = paths.API_KEY_PATH
    worker = YoutubeWorker(dk_file)
    items = worker.get_uploads("UCaNd66xUJjX8VZT6AByVpiw", "2016-10-10T06:20:16.813Z")
    ok = True
    for i in range(0, len(items) - 1):
        date_compare = compare_yt_dates(items[i].get_publish_date(), items[i + 1].get_publish_date())

        if date_compare == 1:
            ok = False
            ic(f"Video: {items[i].get_id()} and {items[i + 1].get_id()}. "
               f"Has publish dates: {items[i].get_publish_date()} and {items[i + 1].get_publish_date()}")

    for item in items:
        publish_fields_equals = item.playlist_item.get_publish_date() == item.video_item.get_publish_date()
        if not publish_fields_equals:
            ok = False
            ic(f"Video: {item.get_id()}. "
               f"Has publish dates: {item.playlist_item.get_publish_date()} and {item.video_item.get_publish_date()}")

    return ok


def test_db_utils() -> bool:
    videos_list = YoutubeVideoList.from_file(TEST_READ_WRITE_DB)
    output_file = TESTS_PATH + "\\" + test_db_utils.__name__ + "temp.txt"

    videos_list.write(output_file)
    if not files_content_equal(TEST_READ_WRITE_DB, output_file):
        return False

    videos_list.write(output_file)
    db_utils.shift(output_file, 7, 3)
    if not files_content_equal(TEST_DB_SHIFT, output_file):
        return False

    videos_list.write(output_file)
    db_utils.move(output_file, "M-vGUWt9BLI", 3)
    if not files_content_equal(TEST_DB_MOVE, output_file):
        return False

    videos_list.write(output_file)
    db_utils.delete(output_file, ["NvRHXnb039Q"])
    if not files_content_equal(TEST_DB_DEL, output_file):
        return False

    videos_list.write(output_file)
    video_1 = YoutubeVideo(video_id="video_0", title="video_0", channel_name="test",
                           published_at="2019-02-17T14:21:09.000Z", number=1, file_extension=FileExtension.MP3,
                           status=YoutubeVideo.STATUS_MISSING)
    video_end = YoutubeVideo(video_id="video_end", title="video_end", channel_name="test",
                             published_at="2022-02-19T17:30:02Z", number=15, file_extension=FileExtension.MP3,
                             status=YoutubeVideo.STATUS_MISSING)
    video_mid = YoutubeVideo(video_id="video_mid", title="video_mid", channel_name="test",
                             published_at="2019-10-24T17:13:57.000Z", number=8, file_extension=FileExtension.MP3,
                             status=YoutubeVideo.STATUS_MISSING)
    video_no_num = YoutubeVideo(video_id="video_no_num", title="video_no_num", channel_name="test",
                                published_at="2020-02-07T17:47:05.000Z", number=-1, file_extension=FileExtension.MP3,
                                status=YoutubeVideo.STATUS_MISSING)
    video_no_num_end = YoutubeVideo(video_id="video_no_num_end", title="video_no_num_end", channel_name="test",
                                    published_at="2023-02-19T17:30:02Z", number=-1,
                                    file_extension=FileExtension.MP3, status=YoutubeVideo.STATUS_MISSING)
    videos = [video_end, video_1, video_mid, video_no_num, video_no_num_end]
    db_utils.insert(output_file, videos)
    if not files_content_equal(TEST_DB_INSERT, output_file):
        return False

    os.remove(output_file)
    return True


def test_playlist_utils() -> bool:
    playlist_list = PlaylistItemList.from_file(TEST_READ_WRITE_PLAYLIST)
    output_file = TESTS_PATH + "\\" + test_playlist_utils.__name__ + "temp.txt"

    # Test read / write consistency
    playlist_list.write(output_file)
    if not files_content_equal(TEST_READ_WRITE_PLAYLIST, output_file):
        return False

    # Test that tracks numbers are added
    # NOTE: Probably not relevant anymore
    # PlaylistItemList.from_file(TEST_ADD_PLAYLIST_TRACKS).write(output_file)
    # playlist_utils.add_missing_track_number(output_file, TEST_ADD_PLAYLIST_TRACKS_DB)
    # if not files_content_equal(TEST_ADD_PLAYLIST_TRACKS_RES, output_file):
    #     return False

    playlist_list.write(output_file)
    playlist_utils.shift(output_file, 21, 3)
    if not files_content_equal(TEST_PLAYLIST_SHIFT, output_file):
        return False

    playlist_list.write(output_file)
    playlist_utils.move(output_file, "https://www.youtube.com/watch?v=ffssuJ5iBxc", 14)
    if not files_content_equal(TEST_PLAYLIST_MOVE, output_file):
        return False

    playlist_list.write(output_file)
    playlist_utils.delete(output_file, ["https://www.youtube.com/watch?v=ffssuJ5iBxc"])
    if not files_content_equal(TEST_PLAYLIST_DEL, output_file):
        return False

    playlist_list.write(output_file)
    item_1 = PlaylistItem("item_1", "https://www.youtube.com/watch?v=test_1xxxxx",
                          PlaylistItem.ITEM_FLAG_DEFAULT, 1)
    item_end = PlaylistItem("item_end", "https://www.youtube.com/watch?v=test_endxxx",
                            PlaylistItem.ITEM_FLAG_DEFAULT, 70)
    item_mid = PlaylistItem("item_mid", "https://www.youtube.com/watch?v=test_midxxx",
                            PlaylistItem.ITEM_FLAG_DEFAULT, 21)
    playlist_utils.insert(output_file, [item_end, item_mid, item_1])
    if not files_content_equal(TEST_PLAYLIST_INSERT, output_file):
        return False

    os.remove(output_file)
    return True


def test_sync_media() -> bool:
    db_file = TEST_SYNC_DB_FILE
    before_files = file.list_files(TEST_SYNC_DB_PATH_BEFORE)
    after_files = file.list_files(TEST_SYNC_DB_PATH_AFTER)

    temp_folder = "\\".join([TEST_SYNC_DB_PATH, "temp"])
    os.mkdir(temp_folder)
    [f.copy(temp_folder) for f in before_files]

    media_utils.sync_media_filenames_with_db(db_file, [temp_folder], FileExtension.MP3)

    temp_files = file.list_files(temp_folder)
    if len(temp_files) != len(after_files):
        print(f"Files len not matching. Expected: {len(after_files)}. Actual: {len(temp_files)}")
        return False

    for f1, f2 in zip(temp_files, after_files):
        temp_file: File = f1
        expected_file: File = f2

        if f1.name != f2.name:
            print(f"Files not equal. Expected: {expected_file.name}. Actual: {temp_file.name}")
            return False

        temp_tags = Ffmpeg.read_metadata(temp_file.get_abs_path())
        expected_tags = Ffmpeg.read_metadata(expected_file.get_abs_path())
        del temp_tags["ENCODER"]
        del expected_tags["ENCODER"]

        if not Ffmpeg.tags_equal(expected_tags, temp_tags):
            print(f"Tags not equal")
            print(f"Expected: {str(expected_tags)}.")
            print(f"Actual: {str(temp_tags)}")
            return False

    [f.delete() for f in temp_files]
    os.rmdir(temp_folder)
    return True


def test_watchers_json() -> bool:
    test_file = TEST_WATCHERS
    watchers = YoutubeWatcher.from_file(test_file)
    output_file = TESTS_PATH + "\\" + test_watchers_json.__name__ + "temp.txt"

    watchers_json = ["[", ",\n".join([watcher.to_json() for watcher in watchers]), "]"]
    file.write(output_file, watchers_json, file.ENCODING_UTF8)

    if not files_content_equal(test_file, output_file):
        return False

    os.remove(output_file)
    return True


#######################################################################################################################
# Main function
#######################################################################################################################
def __main__():
    tests = [
        test_yt_to_py,
        test_db_utils,
        test_playlist_utils,
        test_video_sort_order,
        test_sync_media,
        test_watchers_json,
    ]

    for test in tests:
        ok = test()
        print(f"{test.__name__}: {'OK' if ok else 'NOT_OK'}")


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
