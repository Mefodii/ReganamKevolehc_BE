import os
import googleapiclient.discovery

from utils import File
from ..utils.yt_datetime import compare_yt_dates

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
api_service_name = "youtube"
api_version = "v3"

MAX_RESULTS = 50


class YoutubeWorker:
    def __init__(self, dk_file):

        self.dk = File.get_file_lines(dk_file)[0]
        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=self.dk)

    def get_channel_id_from_name(self, yt_name):
        request = self.youtube.channels().list(
            part="id, contentDetails",
            forUsername=yt_name
        )
        return request.execute()

    def get_channel_uploads_playlist_id(self, yt_id):
        request = self.youtube.channels().list(
            part="contentDetails",
            id=yt_id
        )
        return request.execute()

    # Deprecated
    def get_channel_uploads_from_date2(self, yt_id, yt_date):
        items = []
        next_page = True
        token = ""
        while next_page:
            request = self.youtube.search().list(
                part="snippet,id",
                channelId=yt_id,
                maxResults=MAX_RESULTS,
                order="date",
                publishedAfter=yt_date,
                pageToken=token
            )
            response = request.execute()

            File.append_to_file("debug.txt", response.get('items'))
            File.append_to_file("debug.txt", "")

            items += response.get('items')
            token = response.get('nextPageToken')
            if not response.get('items') or not token:
                next_page = False

        return items

    def get_channel_uploads_from_date(self, yt_id, yt_date):
        uploads_response = self.get_channel_uploads_playlist_id(yt_id)
        uploads_id = uploads_response.get("items")[0].get("contentDetails").get("relatedPlaylists").get("uploads")

        items = []
        next_page = True
        token = ""
        while next_page:
            request = self.youtube.playlistItems().list(
                part="snippet,contentDetails",
                playlistId=uploads_id,
                maxResults=MAX_RESULTS,
                pageToken=token
            )
            response = request.execute()

            for item in response.get('items'):
                published_at = item.get("contentDetails").get("videoPublishedAt")
                if published_at is not None:
                    if compare_yt_dates(published_at, yt_date) == 1:
                        items += [item]

            token = response.get('nextPageToken')
            if not response.get('items') or not token:
                next_page = False

        items = self.remove_livestreams(items)
        return items

    def remove_livestreams(self, items):
        result = []

        for checked_item, original_item in zip(self.get_videos(items), items):
            # If attribute "liveStreamingDetails" exists on checked_item -> it is livestream
            if not checked_item.get("liveStreamingDetails", None):
                result += [original_item]
            else:
                print("Livestream to be ignored: " + checked_item)

        return items

    def get_videos(self, id_list):
        items = []

        chunks = [id_list[x:x + MAX_RESULTS] for x in range(0, len(id_list), MAX_RESULTS)]
        for chunk in chunks:
            comma_chunk = ",".join(chunk)
            request = self.youtube.videos().list(
                part="snippet,liveStreamingDetails",
                id=comma_chunk
            )
            response = request.execute()

            for item in response.get('items'):
                items += [item]

        return items
