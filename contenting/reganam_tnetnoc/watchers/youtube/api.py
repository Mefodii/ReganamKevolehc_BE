import os
import re
from typing import Tuple

# noinspection PyPackageRequirements
import googleapiclient.discovery

from constants.constants import DEFAULT_YOUTUBE_WATCH
from contenting.reganam_tnetnoc.utils.yt_datetime import compare_yt_dates, yt_hours_diff
from utils import file
from utils.string_utils import replace_chars_variations

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

MAX_RESULTS = 50
MAX_DURATION = 32400  # 9 hours


class YoutubeAPIPlaylistItem:
    def __init__(self, data: dict):
        self.data = data
        self.replace_title()

    def get_id(self): return self.data.get("snippet").get("resourceId").get("videoId")

    def get_channel_name(self): return self.data.get("snippet").get("channelTitle")

    def get_title(self): return self.data.get("snippet").get("title")

    def set_title(self, new_title: str): self.data["snippet"]["title"] = new_title

    def replace_title(self): self.set_title(replace_chars_variations(self.get_title()))

    def get_publish_date_old(self) -> str: return self.data.get("snippet", {}).get("publishedAt")

    def get_publish_date(self) -> str: return self.data.get("contentDetails").get("videoPublishedAt")

    def is_video_kind(self): return self.data.get("snippet").get("resourceId").get("kind") == "youtube#video"

    def __repr__(self): return f"{self.data.__repr__()}"


class YoutubeAPIVideoItem:
    def __init__(self, data: dict):
        self.data = data
        self.replace_title()

    def get_id(self): return self.data["id"]
    def get_title(self): return self.data.get("snippet").get("title")

    def set_title(self, new_title: str): self.data["snippet"]["title"] = new_title

    def replace_title(self): self.set_title(replace_chars_variations(self.get_title()))

    def get_publish_date(self) -> str: return self.data.get("snippet").get("publishedAt")

    def is_livestream(self) -> bool: return self.data["snippet"]["liveBroadcastContent"] == "live"

    def is_upcoming(self) -> bool: return self.data["snippet"]["liveBroadcastContent"] == "upcoming"

    def get_channel_id(self) -> str: return self.data["snippet"]["channelId"]

    def get_duration(self) -> str: return self.data["contentDetails"]["duration"]

    def __repr__(self): return f"{self.data.__repr__()}"


class YoutubeAPIItem:
    def __init__(self, playlist_item: YoutubeAPIPlaylistItem = None, video_item: YoutubeAPIVideoItem = None):
        self.playlist_item = playlist_item
        self.video_item = video_item

    @staticmethod
    def sort_by_publish_date(items):
        return sorted(items, key=lambda k: k.get_publish_date())

    def get_id(self):
        if self.playlist_item:
            return self.playlist_item.get_id()

        if self.video_item:
            return self.video_item.get_id()

        raise Exception(f"No data")

    def get_url(self) -> str:
        return DEFAULT_YOUTUBE_WATCH + self.get_id()

    def get_channel_name(self):
        if self.playlist_item:
            return self.playlist_item.get_channel_name()

        raise Exception(f"No data")

    def get_title(self):
        if self.playlist_item:
            return self.playlist_item.get_title()
        if self.video_item:
            return self.video_item.get_title()

        raise Exception(f"No data")

    def get_publish_date(self) -> str:
        if self.playlist_item and self.video_item:
            if self.playlist_item.get_publish_date() != self.video_item.get_publish_date():
                print(f"Warning, something wrong. Same video has different publish date.")
                print(repr(self))

        if self.playlist_item:
            return self.playlist_item.get_publish_date()

        if self.video_item:
            return self.video_item.get_publish_date()

        raise Exception(f"No data")

    def is_livestream(self) -> bool:
        if self.video_item:
            return self.video_item.is_livestream()

        raise Exception(f"No data")

    def is_upcoming(self) -> bool:
        if self.video_item:
            return self.video_item.is_upcoming()

        raise Exception(f"No data")

    def is_short(self) -> bool:
        # TODO - make a http request to check if it's a short (dunno if it will work, requests timeout possible)
        pass

    def has_valid_duration(self) -> bool:
        return 0 < self.get_duration_seconds() <= MAX_DURATION

    def is_video_kind(self):
        if self.playlist_item:
            return self.playlist_item.is_video_kind()

        raise Exception(f"No data")

    def get_channel_id(self) -> str:
        if self.video_item:
            return self.video_item.get_channel_id()

        raise Exception(f"No data")

    def get_duration(self) -> str:
        if self.video_item:
            return self.video_item.get_duration()

        raise Exception(f"No data")

    def get_duration_seconds(self) -> int:
        duration_str = self.get_duration()

        days = re.search(r"\d*D", duration_str)
        hours = re.search(r"\d*H", duration_str)
        minutes = re.search(r"\d*M", duration_str)
        seconds = re.search(r"\d*S", duration_str)

        total_seconds = 0
        if days:
            total_seconds += int(days.group()[:-1]) * 86400
        if hours:
            total_seconds += int(hours.group()[:-1]) * 3600
        if minutes:
            total_seconds += int(minutes.group()[:-1]) * 60
        if seconds:
            total_seconds += int(seconds.group()[:-1])

        return total_seconds

    def __repr__(self):
        return f"Playlist data: {self.playlist_item.__repr__()}.\nVideo data: {self.video_item.__repr__()}"


def merge_items(playlist_items: list[YoutubeAPIPlaylistItem],
                video_items: list[YoutubeAPIVideoItem]) -> list[YoutubeAPIItem]:
    result: dict[str, YoutubeAPIItem] = {item.get_id(): YoutubeAPIItem(playlist_item=item)
                                         for item in playlist_items}

    for item in video_items:
        result[item.get_id()].video_item = item

    for item in result.values():
        if item.video_item is None:
            raise Exception(f"API item has no video_item data: {repr(item)}")

    return list(result.values())


def filter_items(uploads: list[YoutubeAPIItem]) -> list[YoutubeAPIItem]:
    filtered: list[YoutubeAPIItem] = []
    for item in uploads:
        if item.is_upcoming() or item.is_livestream():
            print(f"Api video filtered out: {item}")
            continue

        filtered.append(item)
    return filtered


class YoutubeWorker:

    def __init__(self, dk_file: str):

        self.dk = file.read(dk_file)[0]
        self.youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, developerKey=self.dk)

    def get_uploads_playlist_id(self, channel_id: str) -> str:
        """
        Each YouTube channel has a default "uploads" playlist which contains all the videos
        :param channel_id: IF of the YouTube channel
        :return: ID of the playlist named "uploads"
        """
        request = self.youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()
        uploads_id = response.get("items")[0].get("contentDetails").get("relatedPlaylists").get("uploads")

        return uploads_id

    def get_uploads(self, channel_id: str, min_date: str, max_date: str = None) -> list[YoutubeAPIItem]:
        """
        :param channel_id:
        :param min_date:
        :param max_date:
        :return: uploads for given YouTube id in range min_date < yt_date <= max_date (ignore max_date if None)
        """
        uploads_playlist_id = self.get_uploads_playlist_id(channel_id)

        playlist_items: list[YoutubeAPIPlaylistItem] = []
        has_next_page = True
        token = ""
        reached_yt_date = False
        while has_next_page and not reached_yt_date:
            items, token, has_next_page = self.get_playlist_items(uploads_playlist_id, token)

            for item in items:
                published_at = item.get_publish_date()
                published_at_old = item.get_publish_date_old()
                if published_at is None:
                    print(f'Warning: ignored video with no publish date {item.get_id()}')
                    continue

                if published_at_old and yt_hours_diff(published_at, published_at_old) > 9.0:
                    print(f'Warning: publish date differs. Id: {item.get_id()}. Title: {item.get_title()}')
                    inp_ok = False
                    inp = None
                    while not inp_ok:
                        inp = input(f"Which to use? [M]ain: {published_at} / [S]econdary: {published_at_old} / "
                                    f"[D]efault\n").upper()
                        inp_ok = inp in "MSD"
                    if inp == "S":
                        published_at = published_at_old

                good_min_date = compare_yt_dates(published_at, min_date) == 1
                good_max_date = True if not max_date else compare_yt_dates(published_at, max_date) <= 0
                if good_min_date and good_max_date:
                    playlist_items.append(item)
                elif good_min_date and not good_max_date:
                    continue
                else:
                    reached_yt_date = True

        video_items = self.get_videos([item.get_id() for item in playlist_items])
        uploads = merge_items(playlist_items, video_items)
        uploads = filter_items(uploads)

        # Reverse uploads so it will be ascendent by published_at
        result = uploads[::-1]

        # Note 2023.10.17: a check to be sure that results is still received in
        #  chronological order and API is working as usual
        sorted_uploads = YoutubeAPIItem.sort_by_publish_date(uploads)
        for i1, i2 in zip(sorted_uploads, result):
            i1: YoutubeAPIItem
            i2: YoutubeAPIItem
            if i1 != i2 and i1.get_publish_date() != i2.get_publish_date():
                print("Warning! sort problem", i1, i2)

        return result

    def get_videos(self, id_list: list[str]) -> list[YoutubeAPIVideoItem]:
        items: list[YoutubeAPIVideoItem] = []

        # Breaks id_list in arrays of the length of MAX_RESULTS
        chunks = [id_list[i:i + MAX_RESULTS] for i in range(0, len(id_list), MAX_RESULTS)]
        for chunk in chunks:
            comma_chunk = ",".join(chunk)
            request = self.youtube.videos().list(
                part="snippet,liveStreamingDetails,contentDetails",
                id=comma_chunk
            )
            response = request.execute()
            items += [YoutubeAPIVideoItem(item) for item in response.get('items')]

        if len(id_list) != len(items):
            print("Warning: not all videos extracted!")

        return items

    def get_playlist_items(self, playlist_id: str, page_token: str) \
            -> Tuple[list[YoutubeAPIPlaylistItem], str | None, bool]:
        # Note 2023.10.17: It seems that results are sorted by publish date

        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=playlist_id,
            maxResults=MAX_RESULTS,
            pageToken=page_token
        )
        response = request.execute()
        token = response.get('nextPageToken')
        has_next_page = True
        items = [YoutubeAPIPlaylistItem(item) for item in response.get('items')]

        if not items or not token:
            has_next_page = False

        return items, token, has_next_page

    def get_channel_id_from_video(self, video_id: str) -> str:
        item = self.get_videos([video_id])[0]
        return item.get_channel_id()
