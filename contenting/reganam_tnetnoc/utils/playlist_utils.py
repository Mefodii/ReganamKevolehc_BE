from constants import constants
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItem, PlaylistItemList
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideoList


def shift(playlist_file: str, number: int, step: int = 1):
    """
    All videos with number greater or equal of given number will have its number changed by step.

    Update video file_name with new number
    :param playlist_file:
    :param number:
    :param step: how many position to shift. Negative as well
    :return:
    """
    playlist_list = PlaylistItemList.from_file(playlist_file)
    playlist_list.shift_number(position_start=number, position_end=None, step=step)
    playlist_list.write(playlist_file)


def move(playlist_file: str, video_url: str, new_number: int):
    """
    Find and delete item from current number. Then insert it with new_number

    Playlist file must be sorted
    :param playlist_file:
    :param video_url: full url, with http and stuff
    :param new_number:
    :return:
    """
    playlist_list = PlaylistItemList.from_file(playlist_file)

    item = playlist_list.get_by_url(video_url)
    if item is None:
        raise Exception(f"Item not found in playlist. ID: {video_url}")
    playlist_list.move(item, new_number)

    playlist_list.write(playlist_file)


def insert(playlist_file: str, items: list[PlaylistItem]):
    """
    Insert items to the item.track_nr position and shift all other items down
    :param playlist_file:
    :param items:
    :return:
    """
    playlist_list = PlaylistItemList.from_file(playlist_file)

    for i in items:
        playlist_list.insert(i)

    playlist_list.write(playlist_file)


def delete(playlist_file: str, videos_url: list[str]):
    """
    Find video with given url and delete it from file. All other videos number are shifted by -1.
    :param playlist_file:
    :param videos_url: list with full url, with http and stuff
    :return:
    """
    playlist_list = PlaylistItemList.from_file(playlist_file)

    for url in videos_url:
        item = playlist_list.get_by_url(url)
        if item is None:
            raise Exception(f"Item not found in playlist. ID: {url}")

        playlist_list.delete(item)

    playlist_list.write(playlist_file)


def add_missing_track_number(playlist_file: str, db_file: str):
    """
    If a playlist item has no number, find it in db_file and update playlist item.
    :param playlist_file:
    :param db_file:
    :return:
    """
    videos_list = YoutubeVideoList.from_file(db_file)
    playlist_list = PlaylistItemList.from_file(playlist_file)

    changed = False
    for item in playlist_list.items:
        if item.is_dummy:
            continue

        if item.number is None:
            video_id = item.url.replace(constants.DEFAULT_YOUTUBE_WATCH, "")
            db_video = videos_list.get_by_id(video_id)
            if db_video is None:
                raise Exception(f"Video not found in DB. Video ID: {video_id}")

            item.number = db_video.number
            changed = True

    if changed:
        playlist_list.write(playlist_file)


def check_validity(playlist_file: str, db_file: str) -> bool:
    """
    Check that playlist is sorted.

    Check that all videos from db are in playlist and no extras.
    :param playlist_file:
    :param db_file:
    :return:
    """
    videos = YoutubeVideoList.from_file(db_file).videos
    playlist_list = PlaylistItemList.from_file(playlist_file)

    if not playlist_list.is_sorted():
        return False

    items_dict: dict[str, PlaylistItem] = {item.url.replace(constants.DEFAULT_YOUTUBE_WATCH, ""): item
                                           for item in playlist_list.items}
    valid = True
    for db_video in videos:
        item = items_dict.pop(db_video.video_id, None)
        if not item:
            valid = False
            print(f"Video not found in playlist. Video: {db_video}")

        if item.number != db_video.number:
            valid = False
            print(f"Mismatch number. ID: {db_video.video_id}. DB_NR: {db_video.number}. PL_NR: {item.number}")

    for item in items_dict.values():
        if not item.is_dummy:
            valid = False
            print(f"Extra item in playlist. Item: {item}")

    return valid
