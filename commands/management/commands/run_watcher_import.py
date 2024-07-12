import datetime
from typing import Tuple

import pytz
from django.core.management.base import BaseCommand

from constants import paths
from constants.enums import ContentCategory, DownloadStatus, ContentWatcherSourceType, ContentWatcherStatus, \
    ContentItemType, VideoQuality, TrackStatus
from constants.enums import FileExtension
from contenting.models import ContentWatcher, ContentItem, ContentList, ContentMusicItem, ContentTrack
from contenting.reganam_tnetnoc.model.playlist_item import PlaylistItem, PlaylistItemList, PlaylistChildItem
from contenting.reganam_tnetnoc.watchers.youtube.media import YoutubeVideo
from contenting.reganam_tnetnoc.watchers.youtube.watcher import YoutubeWatcher
from contenting.serializers import ContentWatcherCreateSerializer, ContentListSerializer
from listening.models import Track, Artist, Release, ReleaseTrack
from listening.queryset import ReleaseQuerySet, ReleaseTrackQuerySet, TrackQuerySet
from utils import datetime_utils, file
from utils.datetime_utils import utcnow
from utils.string_utils import normalize_text

DOWNLOAD_STATUS_MAPPING: dict[str, DownloadStatus] = {
    YoutubeVideo.STATUS_NO_STATUS: DownloadStatus.NONE,
    YoutubeVideo.STATUS_UNABLE: DownloadStatus.UNABLE,
    YoutubeVideo.STATUS_DOWNLOADED: DownloadStatus.DOWNLOADED,
    YoutubeVideo.STATUS_MISSING: DownloadStatus.MISSING,
    YoutubeVideo.STATUS_SKIP: DownloadStatus.SKIP,
}

TRACK_SPLIT_FILE = r"E:\Google Drive\ReganamKevolehc\temp_track_split.json"
track_split_data = file.read_json(TRACK_SPLIT_FILE)

RELAX_N_LISTEN_LIST = "Relax'n'Listen (frozen)"
current_imported_list: str | None = None


def find_track_split_data(track_title: str) -> Tuple[list[str], str] | Tuple[None, None]:
    rec: dict | None = track_split_data.get(track_title, None)
    if rec is None:
        return None, None

    return rec["artists"], rec["title"]


def append_to_track_split(track_title: str, artists: list[str], title: str) -> None:
    rec: dict | None = track_split_data.get(track_title, None)
    if rec:
        raise ValueError(f"Title already exists: {track_title}")

    track_split_data[track_title] = {"artists": artists, "title": title}


def get_or_create_content_watcher(watcher: YoutubeWatcher) -> ContentWatcher:
    try:
        content_watcher = ContentWatcher.objects.get(watcher_id=watcher.channel_id)
        if content_watcher.name != watcher.name:
            raise ValueError(f"Content watcher already exists: {watcher.name}")

        return content_watcher
    except ContentWatcher.DoesNotExist:
        category = ContentCategory.MUSIC.value if watcher.download and watcher.file_extension == FileExtension.MP3 \
            else ContentCategory.OTHER.value
        cw_data = {
            "name": watcher.name,
            "category": category,
            "watcher_id": watcher.channel_id,
            "source_type": ContentWatcherSourceType.YOUTUBE.value,
            "status": ContentWatcherStatus.FINISHED.value,
            "check_date": watcher.check_date,
            "download": watcher.download,
            "file_extension": watcher.file_extension,
            "video_quality": watcher.video_quality if watcher.video_quality else VideoQuality.DEFAULT.value,
        }
        cw_serializer = ContentWatcherCreateSerializer(data=cw_data)
        if cw_serializer.is_valid():
            instance = cw_serializer.create(cw_serializer.validated_data)
            return instance
        else:
            raise Exception(cw_serializer.errors)


def get_or_create_content_list(name: str, category: ContentCategory) -> ContentList:
    try:
        content_list = ContentList.objects.get(name=name)
        return content_list
    except ContentList.DoesNotExist:
        cl_data = {
            "name": name,
            "category": category.value,
            "migration_position": 0,
        }
        cl_serializer = ContentListSerializer(data=cl_data)
        if cl_serializer.is_valid():
            instance = cl_serializer.create(cl_serializer.validated_data)
            return instance
        else:
            raise Exception(cl_serializer.errors)


def get_or_create_content_item(content_watcher: ContentWatcher, db_video: YoutubeVideo,
                               playlist_item: PlaylistItem | None) -> ContentItem:
    try:
        content_item = ContentItem.objects.get(item_id=db_video.video_id)
        if content_item.position != db_video.number:
            raise ValueError(f"Position mismatch for item: {content_item}. DB: {content_item.position}. "
                             f"Vid: {db_video.number}")

        return content_item
    except ContentItem.DoesNotExist:
        content_item = ContentItem()

    content_item.item_id = db_video.video_id
    content_item.url = db_video.get_url()
    content_item.title = db_video.title
    content_item.file_name = db_video.file_name if content_watcher.download else ""
    content_item.position = db_video.number
    content_item.download_status = DOWNLOAD_STATUS_MAPPING[db_video.status].value
    content_item.published_at = datetime_utils.yt_to_py(db_video.published_at)
    content_item.content_list = content_watcher.content_list
    content_item.consumed = False
    if playlist_item:
        content_item.consumed = playlist_item.item_flag == PlaylistItem.ITEM_FLAG_CONSUMED
    content_item.save()

    return content_item


def split_track(track_name: str) -> Tuple[list[str], str]:
    sep = " - "
    lib_sep = " <--> "  # for Relax'n'Listen (frozen).txt

    global current_imported_list
    if current_imported_list == RELAX_N_LISTEN_LIST:
        sep_count = track_name.count(lib_sep)
        parts = track_name.split(lib_sep)
    else:
        sep_count = track_name.count(sep)
        parts = track_name.split(sep)

    split_pos = 1
    if sep_count == 0:
        raise ValueError(f"Cannot parse track: {track_name}. T: {track_name}")
    elif sep_count > 1:
        artists, title = find_track_split_data(track_name)
        if artists:
            return artists, title

        message = f"Track has {sep_count} separate items. Select split position between 1-{sep_count}. T: {track_name}"
        split_pos = int(input(message))
        if not (1 <= split_pos <= sep_count):
            raise ValueError(f"Bad split_pos: {split_pos}")

    artists: list[str] = sep.join(parts[:split_pos]).split(", ")
    title = sep.join(parts[split_pos:])

    if sep_count > 1:
        append_to_track_split(track_name, artists, title)

    return artists, title


def blind_search(raw_title: str) -> Track | None:
    try:
        artists, title = split_track(raw_title)
        artist_objects = []
        for artist_name in artists:
            artist_name = artist_name.strip()
            artist = Artist.objects.get(name=artist_name)
            artist_objects.append(artist)

        tracks = Track.objects.filter_exact_artists(artist_objects).filter(title__iexact=title)
        if len(tracks) == 1:
            return tracks[0]
    except (Artist.DoesNotExist, ValueError):
        return None


def get_or_create_track(playlist_item: PlaylistItem | PlaylistChildItem, downloaded: bool, in_library: bool) -> Track:
    track_name = normalize_text(playlist_item.title)
    is_clean = playlist_item.is_clean()

    like = playlist_item.get_like()
    if like and in_library:
        status = TrackStatus.IN_LIBRARY
    elif like and downloaded:
        status = TrackStatus.DOWNLOADED
    elif like:
        status = TrackStatus.LIKE
    elif like is False:
        status = TrackStatus.DISLIKE
    elif playlist_item.is_not_found():
        status = TrackStatus.MISSING
    else:
        status = TrackStatus.NONE

    title = track_name
    artists = []
    if is_clean:
        artists, title = split_track(title)

    artist_objects = []
    for artist_name in artists:
        artist_name = artist_name.strip()
        artist, created = Artist.objects.get_or_create(name=artist_name)
        artist_objects.append(artist)

    try:
        if is_clean:
            tracks = Track.objects.filter_exact_artists(artist_objects).filter(title=title)
            if len(tracks) == 0:
                raise Track.DoesNotExist()
            elif len(tracks) == 1:
                track = tracks[0]
            else:
                raise ValueError(f"Multiple tracks found for {track_name}. Tracks: {tracks}")
        else:
            track = Track.objects.get(title=title, artists__isnull=True)

        db_status = TrackStatus.from_str(track.status)
        new_status = TrackStatus.merge(status, db_status)
        if new_status is None:
            raise ValueError(f"Cannot merge track in DB."
                             f"Item: {playlist_item}. DB Track: {track}")

        if track.is_clean != is_clean:
            raise ValueError(f"Clean mismatch"
                             f"Item: {playlist_item}. DB Track: {track}")

        track.status = new_status.value
        track.save()

        return track
    except Track.DoesNotExist:
        pass

    track = Track()
    track.title = title

    track.status = status.value
    track.is_clean = is_clean
    track.double_checked = not is_clean

    track.save()
    if artist_objects:
        track.artists.set(artist_objects)

    return track


def get_or_create_content_music_item(content_list: ContentList, playlist_item: PlaylistItem,
                                     db_video: YoutubeVideo | None) -> ContentMusicItem:
    title = normalize_text(playlist_item.title)

    content_items = ContentMusicItem.objects.filter_by_content_list(content_list.id).filter(
        position=playlist_item.number)
    if content_items.count() == 1:
        content_item = content_items[0]
        if content_item.title != title and (db_video and content_item.title != db_video.title):
            raise ValueError(f"Title mismatch. Content list: {content_list}. Title: {title}. "
                             f"Title: {content_item.title}")
        return content_item
    if content_items.count() > 1:
        raise ValueError(f"Multiple content items found. Content list: {content_list}. ")

    content_item = ContentMusicItem()
    content_item.title = title
    content_item.position = playlist_item.number
    content_item.download_status = DownloadStatus.NONE.value
    content_item.published_at = utcnow()
    content_item.content_list = content_list
    content_item.comment = playlist_item.comment

    if playlist_item.parsed_items:
        content_item.type = ContentItemType.PLAYLIST.value
    elif playlist_item.is_track():
        content_item.type = ContentItemType.SINGLE.value
    elif playlist_item.is_notmusic():
        content_item.type = ContentItemType.NOT_MUSIC.value
    else:
        content_item.type = ContentItemType.UNKNOWN.value

    content_item.parsed = False

    if db_video:
        content_item.url = db_video.get_url()
        content_item.item_id = db_video.video_id
        content_item.title = db_video.title
        content_item.file_name = db_video.file_name
        content_item.position = db_video.number
        content_item.download_status = DOWNLOAD_STATUS_MAPPING[db_video.status].value
        content_item.published_at = datetime_utils.yt_to_py(db_video.published_at)

    content_item.save()

    return content_item


def get_or_create_content_track(content_item: ContentMusicItem, track: Track | None,
                                playlist_item: PlaylistItem | PlaylistChildItem) -> ContentTrack:
    title = normalize_text(playlist_item.title)
    position = 1 if isinstance(playlist_item, PlaylistItem) else playlist_item.number

    content_tracks = ContentTrack.objects.filter(content_item=content_item, position=position)
    if content_tracks.count() == 1:
        content_track = content_tracks[0]
        if content_track.title != title:
            raise ValueError(f"Title mismatch. Content item: {content_item}. Title: {title}. "
                             f"Title: {content_track.title}")

        if track:
            replace_with_clean = track.is_clean and content_track.track and not content_track.track.is_clean
            if content_track.track is None or replace_with_clean:
                content_track.track = track
                content_track.save()

        return content_track
    if content_tracks.count() > 1:
        raise ValueError(f"Multiple tracks found for {content_item}. Tracks: {content_tracks}")

    content_track = ContentTrack()
    content_track.title = title
    content_track.content_item = content_item
    content_track.needs_edit = False
    content_track.track = track
    content_track.comment = playlist_item.comment
    content_track.is_track = True if track else False
    content_track.position = position

    if not isinstance(playlist_item, PlaylistItem):
        content_track.start_time = playlist_item.get_start_time()

    content_track.save()

    return content_track


def get_or_create_release(artists: list[Artist], name: str, year: int | None, release_type: str) -> Release:
    try:
        releases: ReleaseQuerySet[Release] = Release.objects.filter_exact_artists(artists).filter(name=name)
        if len(releases) == 0:
            raise Release.DoesNotExist()
        elif len(releases) == 1:
            release: Release = releases[0]
        else:
            raise ValueError(f"Multiple releases found for {name}. Releases: {releases}")

        if release.published_at and year and release.published_at.year != year:
            raise ValueError(f"Year mismatch. Expected: {release.published_at.year}. "
                             f"Got: {year}. ")

        if release.type != release_type:
            raise ValueError(f"ReleaseType mismatch. Expected: {release.type}. Got: {release_type}. ")

        return release
    except Release.DoesNotExist:
        pass

    release = Release()
    release.name = name
    release.type = release_type
    if year:
        release.published_at = datetime.datetime(year=year, month=1, day=1, tzinfo=pytz.UTC)

    release.save()
    release.artists.set(artists)

    return release


def get_or_create_release_track(release: Release, track: Track, position: int, comment: str) -> ReleaseTrack:
    try:
        rts: ReleaseTrackQuerySet[ReleaseTrack] = ReleaseTrack.objects.filter(release=release, position=position)
        if len(rts) == 0:
            raise ReleaseTrack.DoesNotExist()
        elif len(rts) == 1:
            release_track: ReleaseTrack = rts[0]
        else:
            raise ValueError(f"Multiple releases found for {release} pos: {position}. Releases: {rts}")

        if release_track.track != track:
            raise ValueError(f"Track mismatch. Expected: {release_track}. Got: {track}. ")

        return release_track
    except ReleaseTrack.DoesNotExist:
        pass

    release_track = ReleaseTrack()

    release_track.position = position
    release_track.comment = comment
    release_track.release = release
    release_track.track = track

    release_track.save()


def import_music_item(content_list: ContentList, playlist_item: PlaylistItem,
                      video_item: YoutubeVideo | None, dl_pos: int, lib_pos: int):
    content_item = get_or_create_content_music_item(content_list, playlist_item, video_item)
    if content_item.type == ContentItemType.PLAYLIST.value:
        for child in playlist_item.parsed_items:
            track: Track | None = None
            if child.is_track():
                track = get_or_create_track(child, downloaded=playlist_item.number <= dl_pos,
                                            in_library=playlist_item.number <= lib_pos)

            get_or_create_content_track(content_item, track, child)
    elif content_item.type == ContentItemType.SINGLE.value:
        track = get_or_create_track(playlist_item, downloaded=playlist_item.number <= dl_pos,
                                    in_library=playlist_item.number <= lib_pos)
        get_or_create_content_track(content_item, track, playlist_item)


def import_watcher(watcher: YoutubeWatcher) -> ContentWatcher:
    content_watcher = get_or_create_content_watcher(watcher)

    if not watcher.db_videos.is_sorted():
        raise ValueError(f"Watcher has videos not sorted. Watcher: {watcher}")
    video_items = watcher.db_videos.get_sorted()

    ids = set(video.video_id for video in video_items)
    if len(ids) != len(video_items):
        raise ValueError(f"Id duplicates in watcher: {watcher}")

    if content_watcher.category == ContentCategory.MUSIC.value:

        global current_imported_list
        current_imported_list = content_watcher.content_list.name

        for video_item in video_items:
            playlist_item = watcher.playlist_items.get_by_url(video_item.get_url())
            dl_pos = watcher.playlist_items.downloaded_position
            lib_pos = watcher.playlist_items.in_lib_position
            if playlist_item.number != video_item.number:
                raise ValueError(f"Different number on item: {video_item}")

            import_music_item(content_watcher.content_list, playlist_item, video_item, dl_pos, lib_pos)
    else:
        for video_item in video_items:
            playlist_item: PlaylistItem | None = watcher.playlist_items.get_by_url(video_item.get_url())
            if playlist_item and playlist_item.number != video_item.number:
                raise ValueError(f"Different number on item: {video_item}")

            get_or_create_content_item(content_watcher, video_item, playlist_item)

    print(f"Finished import for: {watcher.name}")
    file.write_json(TRACK_SPLIT_FILE, track_split_data)
    return content_watcher


def import_watchers():
    watchers_file = paths.YOUTUBE_WATCHERS_PATH
    watchers: list[YoutubeWatcher] = YoutubeWatcher.from_file(watchers_file)
    for watcher in watchers:
        import_watcher(watcher)


def import_artist():
    def parse_release_data(item: PlaylistItem) -> Tuple[str, str, int | None]:
        rt = item.title.strip()[1:15].replace("]", "").strip()
        yyyy = item.title.strip()[16:20]
        yyyy = None if yyyy == "xxxx" else int(yyyy)
        t = item.title.strip()[23:].strip()
        return rt, t, yyyy

    artist_files = file.list_files(r"E:\Google Drive\Mu\plist\Artists")
    for f in artist_files:
        # if f.get_plain_name() != "Alternosfera":
        #     continue

        file_path = f.get_abs_path()

        item_list = PlaylistItemList.from_file(file_path, is_watcher=False)
        artist_name = item_list.find_artist()
        check_data = item_list.find_date()
        alias = item_list.find_alias()

        artist, created = Artist.objects.get_or_create(name=artist_name)

        if check_data:
            y, m, d = [int(x) for x in check_data.split(".")]
            artist.check_date = datetime.datetime(y, m, d, tzinfo=pytz.UTC)
            artist.monitoring = True
            artist.save()

        if alias:
            artist.alias = artist.build_alias(alias)
            artist.save()

        for playlist_item in item_list.items:
            if playlist_item.is_dummy:
                continue

            if playlist_item.parsed_items or playlist_item.is_unknownrelease():
                release_type, title, year = parse_release_data(playlist_item)
                release = get_or_create_release([artist], title, year, release_type)
                if playlist_item.is_unknownrelease():
                    release.unknown_playlist = True
                    release.save()

                for i, child in enumerate(playlist_item.parsed_items, start=1):
                    if i != child.number:
                        raise ValueError(f"Number mismatch for item: {playlist_item}. Got: {child.number}. "
                                         f"Expected: {i}")
                    if not child.is_track():
                        raise ValueError(f"Unexpected non track: {child}")

                    downloaded = child.item_flag.startswith("^")
                    in_lib = downloaded
                    track = get_or_create_track(child, downloaded=downloaded, in_library=in_lib)
                    get_or_create_release_track(release, track, child.number, child.comment)

            else:
                downloaded = playlist_item.item_flag.startswith("^")
                in_lib = downloaded
                if not playlist_item.is_track():
                    raise ValueError(f"Unexpected non track: {playlist_item}")
                get_or_create_track(playlist_item, downloaded=downloaded, in_library=in_lib)

        print(f"Imported: {artist_name.ljust(30)} - {check_data.ljust(15) if check_data else '.' * 15}")
        file.write_json(TRACK_SPLIT_FILE, track_split_data)


def import_list():
    other_files = file.list_files(r"E:\Google Drive\Mu\plist\otherlists")
    for f in other_files:
        list_name = f.get_plain_name()
        file_path = f.get_abs_path()

        # if list_name == "Relax'n'Listen (frozen)":
        #     continue

        item_list = PlaylistItemList.from_file(file_path, is_watcher=False)
        dl_pos = item_list.downloaded_position
        lib_pos = item_list.in_lib_position

        category = ContentCategory.MUSIC
        content_list = get_or_create_content_list(list_name, category)

        global current_imported_list
        current_imported_list = content_list.name

        position = 1
        for playlist_item in item_list.items:
            if playlist_item.is_dummy:
                continue

            if position % 3000 == 0:
                print(position)

            import_music_item(content_list, playlist_item, None, dl_pos, lib_pos)
            position += 1

        print(f"Finished import for: {list_name}")
        file.write_json(TRACK_SPLIT_FILE, track_split_data)


def import_chilledcat():
    playlist_file = r"E:/Google Drive/Mu/plist/ChilledCat.txt"
    watcher = YoutubeWatcher("ChilledCat", "dead_channel", "2024-07-07T14:39:28.552Z", 316,
                             FileExtension.MP3, True,
                             playlist_file, None)

    content_watcher = import_watcher(watcher)
    content_watcher.status = ContentWatcherStatus.DEAD.value
    content_watcher.save()


def reassign_to_clean_tracks():
    tracks: TrackQuerySet[Track] = Track.objects.filter(is_clean=False)
    for track in tracks:
        track: Track
        clean_track = blind_search(track.title)
        if clean_track:
            clean_track.merge(track)


class Command(BaseCommand):
    def handle(self, **options):
        pass
        import_list()
        import_watchers()
        import_chilledcat()
        import_artist()
        reassign_to_clean_tracks()
