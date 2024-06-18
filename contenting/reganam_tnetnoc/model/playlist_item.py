from typing import Self

from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from utils import file


class PlaylistItem:
    START_POS_ITEM_FLAG = 0
    START_POS_TITLE = 5
    START_POS_URL = 115
    START_POS_NUMBER = 167

    ITEM_FLAG_DEFAULT = " [ ]"
    ITEM_FLAG_MISSING = " [@]"
    ITEM_FLAG_SKIP = " [N]"
    ITEM_FLAG_CONSUMED = " [X]"

    DUMMY = "!DUMMY!"

    def __init__(self, title: str, url: str, item_flag: str, number: int = None):
        self.title = title
        self.url = url
        self.item_flag = item_flag
        self.number = number
        # Note: currently no special handling for children.
        # Every line which is under this item and until next PlaylistItem is considered as child.
        self.children: list[str] = []
        self.is_dummy = True if title == PlaylistItem.DUMMY else False

    @classmethod
    def from_youtubevideo(cls, video: YoutubeVideo):
        item_flag = PlaylistItem.ITEM_FLAG_DEFAULT
        if video.status in (YoutubeVideo.STATUS_MISSING, YoutubeVideo.STATUS_UNABLE):
            item_flag = PlaylistItem.ITEM_FLAG_MISSING
        if video.status == YoutubeVideo.STATUS_SKIP:
            item_flag = PlaylistItem.ITEM_FLAG_SKIP

        obj = PlaylistItem(video.title, video.get_url(), item_flag, video.number)
        return obj

    @classmethod
    def from_str(cls, line: str):
        item_flag = line[PlaylistItem.START_POS_ITEM_FLAG:PlaylistItem.START_POS_TITLE].rstrip()
        title = line[PlaylistItem.START_POS_TITLE:PlaylistItem.START_POS_URL].rstrip()
        url = line[PlaylistItem.START_POS_URL:PlaylistItem.START_POS_NUMBER].rstrip()
        number = int(line[PlaylistItem.START_POS_NUMBER:].rstrip())
        obj = PlaylistItem(title, url, item_flag, number)
        return obj

    @classmethod
    def dummy(cls):
        return PlaylistItem(PlaylistItem.DUMMY, "", "")

    @staticmethod
    def is_playlist_str(line: str) -> bool:
        # Keeping it simple atm
        return line[1:2] in "[{"

    def append_child(self, child: str):
        self.children.append(child)

    def __str__(self):
        if self.is_dummy:
            return PlaylistItem.DUMMY

        s = "".ljust(PlaylistItem.START_POS_ITEM_FLAG) + self.item_flag
        s = s.ljust(PlaylistItem.START_POS_TITLE) + self.title
        s = s.ljust(PlaylistItem.START_POS_URL) + self.url
        s = s.ljust(PlaylistItem.START_POS_NUMBER) + str(self.number)
        return s


class PlaylistItemList:
    def __init__(self, data: list[PlaylistItem]):
        self.items = data

    @staticmethod
    def append_videos(file_path: str, videos: list[YoutubeVideo]):
        track_list = [str(PlaylistItem.from_youtubevideo(video)) for video in videos]
        if len(track_list) > 0:
            file.append(file_path, track_list)

    @classmethod
    def from_file(cls, file_path: str, empty_if_not_found: bool = False) -> Self:
        if not file.exists(file_path):
            if empty_if_not_found:
                return cls([])
            raise Exception(f"File not found: {file_path}")

        playlist_data = file.read(file_path, file.ENCODING_UTF8)

        items = []
        item = None
        for line in playlist_data:
            if PlaylistItem.is_playlist_str(line):
                item = PlaylistItem.from_str(line)
                items.append(item)
            else:
                if not item:
                    item = PlaylistItem.dummy()
                    items.append(item)

                item.append_child(line)

        return cls(items)

    def write(self, file_path: str) -> None:
        """
        Write to file_path string representation of all items
        :param file_path:
        :return:
        """
        res = []
        for item in self.items:
            if not item.is_dummy:
                res.append(str(item))

            [res.append(child) for child in item.children]
        file.write(file_path, res, file.ENCODING_UTF8)

    def move(self, item: PlaylistItem, new_number: int):
        if item.number == new_number:
            print(f"Video already has this number. Move canceleld. Video url: {item.url}. Number: {new_number}")
            return

        self.delete(item)
        item.number = new_number
        self.insert(item)

    def insert(self, item: PlaylistItem) -> None:
        """
        Shift up by 1 all items with number higher than current item, then insert given item
        :param item:
        :return:
        """
        if self.get_by_url(item.url):
            raise Exception(f"Item already exists in playlist. ID: {item.url}")

        self.shift_number(position_start=item.number, position_end=None, step=1)

        inserted = False
        for i in range(len(self.items)):
            if self.items[i].is_dummy:
                continue

            if self.items[i].number > item.number:
                self.items.insert(i, item)
                inserted = True
                break

        if not inserted:
            self.items.append(item)

    def delete(self, item: PlaylistItem):
        """
        Remove item, then all items after removed item are shifted down by 1.
        :param item:
        :return:
        """
        if item not in self.items:
            raise Exception(f"Item not found in playlist. ID: {item.url}")

        self.items.remove(item)
        self.shift_number(position_start=item.number, position_end=None, step=-1)

    def shift_number(self, position_start: int, position_end: int = None, step: int = 1):
        """
        All items within range position_start <= item.number <= position_end will have its number changed by step.

        Items are mutated with new position number
        :param position_start: video number start position; inclusive
        :param position_end: video number end position; inclusive
        :param step: how many position to shift. Negative as well
        :return:
        """
        for item in self.items:
            if item.is_dummy:
                continue

            if position_start <= item.number <= (position_end or float('inf')):
                item.number += step
                if item.number <= 0:
                    raise Exception(f"Number <= 0 not allowed. Video ID: {item.url}")

    def get_by_url(self, url: str) -> PlaylistItem | None:
        """
        :param url:
        :return: First PlaylistItem with given url. None if not found.
        """
        for i in range(len(self.items)):
            if self.items[i].url == url:
                return self.items[i]

        return None

    def is_sorted(self) -> bool:
        """
        :return: True if all items in list are sorted ascending by number, no duplicates
        """
        expected_number = 1
        for item in self.items:
            if item.is_dummy:
                continue

            if item.number != expected_number:
                print(f"Item has unsorted number: {item.number}. Item: {item}. Expected number: {expected_number}")
                return False
            expected_number += 1

        return True
