from __future__ import annotations

from typing import Self

from constants.enums import DownloadStatus
from contenting.models import ContentMusicItem
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from utils import file

DEFAULT = " "
MISSING = "@"
NOT_MUSIC = "N"
LIKE = "X"
DISLIKE = "-"
DUPLICATE = "L"
UNKNOWN_RELEASE = "?"

DOWNLOADED_SEP = " ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
IN_LIB_SEP = ' """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""'


def is_like(flag: str) -> bool:
    return flag.upper() == LIKE


def is_dislike(flag: str) -> bool:
    return flag.upper() == DISLIKE


def is_not_found(flag: str):
    return flag.upper() == MISSING


class PlaylistItem:
    POS_STATUS = 2

    START_POS_ITEM_FLAG = 0
    START_POS_TITLE = 5
    START_POS_URL = 115
    START_POS_NUMBER = 167

    ITEM_FLAG_DEFAULT = f" [{DEFAULT}]"
    ITEM_FLAG_MISSING = f" [{MISSING}]"
    ITEM_FLAG_SKIP = f" [{NOT_MUSIC}"
    ITEM_FLAG_CONSUMED = f" [{LIKE}]"
    ITEM_FLAG_DISLIKE = f" [{DISLIKE}]"

    DUMMY = "!DUMMY!"

    def __init__(self, title: str, url: str, item_flag: str, number: int = None):
        self.title = title
        self.url = url
        self.item_flag = item_flag
        self.number = number
        # Note: currently no special handling for children.
        # Every line under this item and until the next PlaylistItem is considered as child.
        self.children: list[str] = []
        self.is_dummy = True if title == PlaylistItem.DUMMY else False

        # Note: I hope these are temporary, needed for importing to Django
        self.comment = ""
        self.parsed_items: list[PlaylistChildItem] = []

    def deep_parse(self):
        self.comment = self.extract_comment()
        self.parsed_items = self.parse_children()

    def is_track(self) -> bool:
        flag = self.item_flag[PlaylistItem.POS_STATUS].upper()
        return flag not in "".join([MISSING, DEFAULT, NOT_MUSIC])

    def is_notmusic(self) -> bool:
        flag = self.item_flag[PlaylistItem.POS_STATUS].upper()
        return flag == NOT_MUSIC

    def is_unknownrelease(self) -> bool:
        flag = self.item_flag[PlaylistItem.POS_STATUS].upper()
        return flag == UNKNOWN_RELEASE

    def is_not_found(self):
        return is_not_found(self.item_flag[PlaylistItem.POS_STATUS])

    def get_like(self) -> bool | None:
        if self.is_like():
            return True
        if self.is_dislike():
            return False
        return None

    def is_like(self) -> bool:
        return is_like(self.item_flag[PlaylistItem.POS_STATUS])

    def is_dislike(self) -> bool:
        return is_dislike(self.item_flag[PlaylistItem.POS_STATUS])

    def is_clean(self):
        return "{" in self.item_flag

    def parse_children(self) -> list[PlaylistChildItem]:
        if self.is_dummy:
            return []

        items = []
        item = None
        for child in self.children:
            if self.is_track_child(child):
                item = PlaylistChildItem.from_str(child, len(items) + 1)
                items.append(item)
            else:
                if not item:
                    continue

                if child in [DOWNLOADED_SEP, IN_LIB_SEP]:
                    continue

                comment = PlaylistChildItem.parse_comment(child)
                if item.comment:
                    raise ValueError(f"Child already has comment: {item}. Item: {self}")
                item.comment = comment

        return items

    def extract_comment(self) -> str:
        if self.is_dummy:
            return ""

        comment = ""
        for child in self.children:
            if child in [DOWNLOADED_SEP, IN_LIB_SEP]:
                continue
            if self.is_track_child(child):
                return comment

            if child.startswith("  # - "):
                if comment:
                    raise ValueError(f"Multiple comments: {str(self)}")
                comment += child.replace("  # - ", "")
            else:
                raise ValueError(f"Unknown comment type: {str(self)}")

        return comment

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
    def from_content_item(cls, item: ContentMusicItem):
        item_flag = PlaylistItem.ITEM_FLAG_DEFAULT
        if item.download_status in (DownloadStatus.MISSING.value, DownloadStatus.UNABLE.value):
            item_flag = PlaylistItem.ITEM_FLAG_MISSING
        if item.download_status == DownloadStatus.SKIP.value:
            item_flag = PlaylistItem.ITEM_FLAG_SKIP

        obj = PlaylistItem(item.title, item.url, item_flag, item.position)
        return obj

    @classmethod
    def from_str(cls, line: str, default_number: int = None):
        item_flag = line[PlaylistItem.START_POS_ITEM_FLAG:PlaylistItem.START_POS_TITLE].rstrip()
        title = line[PlaylistItem.START_POS_TITLE:PlaylistItem.START_POS_URL].rstrip()

        url = ""
        number = default_number
        try:
            url = line[PlaylistItem.START_POS_URL:PlaylistItem.START_POS_NUMBER].rstrip()
            # TODO: temporary hack to import the-stolen-beat
            if url.startswith("https://open.spotify.com"):
                url = line[PlaylistItem.START_POS_URL:].rstrip()
            else:
                number = int(line[PlaylistItem.START_POS_NUMBER:].rstrip())
        except Exception as e:
            if not default_number:
                raise e

        obj = PlaylistItem(title, url, item_flag, number)
        return obj

    @classmethod
    def dummy(cls):
        return PlaylistItem(PlaylistItem.DUMMY, "", "")

    @staticmethod
    def is_playlist_str(line: str) -> bool:
        # Keeping it simple atm
        return line[1:2] in "[{"

    # TODO: 2025-05-23 - To be deteled
    # def has_track_child(self) -> bool:
    #     return any(self.is_track_child(child) for child in self.children)

    @staticmethod
    def is_track_child(child: str) -> bool:
        return PlaylistChildItem.is_playlist_item(child)

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

    def __repr__(self):
        return self.__str__()


class PlaylistChildItem:
    POS_STATUS = 5

    START_POS_ITEM_FLAG = 0
    START_POS_TIMESTAMP = 8
    END_POS_TIMESTAMP = 16
    START_POS_NUMBER = 19
    END_POS_NUMBER = 23
    START_POS_TITLE = 19
    START_POS_TITLE_NUMBERED = 26

    def __init__(self, title: str, item_flag: str, number: int, timestamp: str, comment: str):
        self.title = title
        self.item_flag = item_flag
        self.number = number
        self.timestamp = timestamp
        self.comment = comment

    def is_track(self) -> bool:
        return self.item_flag[PlaylistChildItem.POS_STATUS].upper() != NOT_MUSIC

    def get_like(self) -> bool | None:
        if self.is_like():
            return True
        if self.is_dislike():
            return False
        return None

    def is_like(self) -> bool:
        return is_like(self.item_flag[PlaylistChildItem.POS_STATUS])

    def is_dislike(self) -> bool:
        return is_dislike(self.item_flag[PlaylistChildItem.POS_STATUS])

    def is_not_found(self):
        return is_not_found(self.item_flag[PlaylistItem.POS_STATUS])

    def is_clean(self):
        return "{" in self.item_flag

    def get_start_time(self) -> int | None:
        hh, mm, ss = self.timestamp.split(":")
        if hh == "xx":
            return None

        return int(hh) * 60 * 60 + int(mm) * 60 + int(ss)

    @classmethod
    def from_str(cls, line: str, number: int, comment: str = ""):
        item_flag = line[PlaylistChildItem.START_POS_ITEM_FLAG:PlaylistChildItem.START_POS_TIMESTAMP].rstrip()
        timestamp = line[PlaylistChildItem.START_POS_TIMESTAMP:PlaylistChildItem.END_POS_TIMESTAMP].rstrip()

        if not PlaylistChildItem.is_valid_timestamp(timestamp):
            raise ValueError(f"Invalid timestamp: {timestamp}. Line: {line}")
        if line[PlaylistChildItem.END_POS_TIMESTAMP:PlaylistChildItem.END_POS_TIMESTAMP + 3] != " | ":
            raise ValueError(f"Invalid child: {line}")

        title = line[PlaylistChildItem.START_POS_TITLE:].rstrip()

        if line[23:26] == " | ":
            inner_number = int(line[PlaylistChildItem.START_POS_NUMBER:PlaylistChildItem.END_POS_NUMBER].rstrip())
            if inner_number != number:
                raise ValueError(f"Invalid child number. Received: {number}. Parse: {inner_number}")
            title = line[PlaylistChildItem.START_POS_TITLE_NUMBERED:].rstrip()

        obj = PlaylistChildItem(title, item_flag, number, timestamp, comment)
        return obj

    @staticmethod
    def is_valid_timestamp(timestamp: str) -> bool:
        if timestamp[2] != ":" or timestamp[5] != ":":
            return False
        ts_no_colon = timestamp.replace(":", "")
        if ts_no_colon == "xxxxxx":
            return True
        try:
            int(ts_no_colon)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_playlist_item(child: str) -> bool:
        return child[4:5] in "[{"

    @staticmethod
    def parse_comment(line: str) -> str:
        if not line.startswith("     # - "):
            raise ValueError(f"Invalid comment: {line}")

        return line.replace("     # - ", "").strip()

    def __str__(self):
        s = "".ljust(PlaylistChildItem.START_POS_ITEM_FLAG) + self.item_flag
        s = s.ljust(PlaylistChildItem.START_POS_TIMESTAMP) + self.timestamp
        s += " | " + str(self.number) + " | " + self.title
        return s

    def __repr__(self):
        return self.__str__()


class PlaylistItemList:
    def __init__(self, playlist_items: list[PlaylistItem], is_watcher: bool = True):
        self.is_watcher = is_watcher
        self.downloaded_position = 0
        self.in_lib_position = -1
        self.items = playlist_items

        for item in self.items:
            if DOWNLOADED_SEP in "".join(item.children):
                self.downloaded_position = 0 if item.is_dummy else item.number

            if IN_LIB_SEP in "".join(item.children):
                self.in_lib_position = 0 if item.is_dummy else item.number

        if self.in_lib_position == -1:
            self.in_lib_position = self.downloaded_position

    def find_artist(self) -> str | None:
        return self.find_in_artist("-> Name: ")

    def find_date(self) -> str | None:
        return self.find_in_artist("-> Date: ")

    def find_alias(self) -> list[str] | None:
        alias = self.find_in_artist("-> Alias: ")
        if alias:
            return alias.split(", ")
        return None

    def find_in_artist(self, pattern: str) -> str | None:
        if not self.items or not self.items[0].is_dummy:
            return None

        for child in self.items[0].children:
            if child.startswith(pattern):
                return child.replace(pattern, "").strip()

        return None

    @staticmethod
    def append_videos(file_path: str, videos: list[YoutubeVideo]):
        track_list = [str(PlaylistItem.from_youtubevideo(video)) for video in videos]
        if len(track_list) > 0:
            file.append(file_path, track_list)

    @staticmethod
    def append_content_items(file_path: str, items: list[ContentMusicItem]):
        track_list = [str(PlaylistItem.from_content_item(item)) for item in items]
        if len(track_list) > 0:
            file.append(file_path, track_list)

    @classmethod
    def from_file(cls, file_path: str, empty_if_not_found: bool = False, is_watcher: bool = True) -> Self:
        if not file.exists(file_path):
            if empty_if_not_found:
                return cls([])
            raise Exception(f"File not found: {file_path}")

        playlist_data = file.read(file_path, file.ENCODING_UTF8)

        items: list[PlaylistItem] = []
        item = None
        for line in playlist_data:
            if PlaylistItem.is_playlist_str(line):
                default_number = None if is_watcher else len(items) + 1
                item = PlaylistItem.from_str(line, default_number)
                items.append(item)
            else:
                # All the lines which are not playlist items are children of the previous item
                if not item:
                    # All the lines before the first playlist item are children of the dummy item
                    item = PlaylistItem.dummy()
                    items.append(item)

                item.append_child(line)

        [item.deep_parse() for item in items]
        return cls(items, is_watcher)

    def write(self, file_path: str) -> None:
        """
        Write to file_path string representation of all items
        :param file_path:
        :return:
        """
        if not self.is_watcher:
            raise Exception("Not allowed to write a non watcher")

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
        Shift up by 1 all items with number higher than current item, then insert the given item
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
        Remove the item, then all items after the removed item are shifted down by 1.
        :param item:
        :return:
        """
        if item not in self.items:
            raise Exception(f"Item not found in playlist. ID: {item.url}")

        self.items.remove(item)
        self.shift_number(position_start=item.number, position_end=None, step=-1)

    def shift_number(self, position_start: int, position_end: int = None, step: int = 1):
        """
        All items within the range position_start <= item.number <= position_end will have its number changed by step.

        Items are mutated with the new position number
        :param position_start: video number start position; inclusive
        :param position_end: video number end position; inclusive
        :param step: how many positions to shift. Negative as well
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
        :return: True if all items in the list are sorted ascending by number, no duplicates
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
