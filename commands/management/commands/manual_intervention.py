from typing import TypeVar

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import QuerySet

from commands.management.commands.run_watcher_legacy import RELAX_N_LISTEN_LIST
from constants.enums import TrackStatus, WatchingStatus
from constants.paths import NORMALIZATION_PATH
from contenting.models import ContentTrack, ContentMusicItem, ContentList, ContentItem
from contenting.reganam_tnetnoc.main import short_scripts
from listening.models import Track, Artist, ReleaseTrack, Release, ReleaseArtists
from utils import file
from utils.string_utils import normalize_text
from watching.models import Video


def print_counts():
    print("ContentMusicItem".ljust(20), ContentMusicItem.objects.count())
    print("ContentTrack".ljust(20), ContentTrack.objects.count())
    print("Artist".ljust(20), Artist.objects.count())
    print("Release".ljust(20), Release.objects.count())
    print("ReleaseTrack".ljust(20), ReleaseTrack.objects.count())
    print("Track".ljust(20), Track.objects.count())


def print_dead_tracks():
    objs: QuerySet = Track.objects.filter_dead()
    print(f"Regular Dead: {objs.count()}")
    for o in objs:
        print(o.id, o)

    objs: QuerySet = Track.objects.filter_dcheck_dead()
    print(f"Double Check Dead: {objs.count()}")
    for o in objs:
        print(o.id, o)

    objs = Release.objects.filter_dead()
    print(f"Dead Release: {objs.count()}")
    for o in objs:
        print(o.id, o)

    objs: QuerySet = ReleaseTrack.objects.filter_dead()
    print(f"Dead ReleaseTrack: {objs.count()}")
    for o in objs:
        print(o.id, o)

    objs: QuerySet = Artist.objects.filter_dead()
    print(f"Dead artists: {objs.count()}")
    for o in objs:
        print(o.id, o)


def compare_files():
    f1 = r"C:\Users\Mefodii\Downloads\f1.txt"
    f2 = r"C:\Users\Mefodii\Downloads\f2.txt"

    file.files_content_equal(f1, f2, True)


def multiple_artist():
    tracks = Track.objects.all()
    for track in tracks:
        if len(track.artists.all()) > 1:
            print(str(track) + " --- " + str(track.artists.all()))


def print_artist_tracks():
    a = Artist.objects.get(name="RADIO ЧАЧА")
    print(a)
    for track in a.tracks.all():
        track: Track
        print(track.id, track.content_tracks.all())


def get_cmi():
    items = ContentMusicItem.objects.filter(title__contains="quickly, quickly")
    for i in items:
        print(i.id)


def find_similar_tracks():
    # TODO: function to check for duplicate tracks (same artistst and same title) ignore case
    pass


M = TypeVar("M", bound=models.Model)


def delete_all_music():
    def delete_table_objects(table: type[M]) -> None:
        while True:
            pks: list = table.objects.values_list("pk", flat=True)[:7000]
            if len(pks) == 0:
                break

            table.objects.filter(pk__in=pks).delete()

    delete_table_objects(Artist)
    delete_table_objects(Track)
    delete_table_objects(Release)
    delete_table_objects(ReleaseTrack)
    delete_table_objects(ContentMusicItem)


def clean_dead_music():
    Track.clean_dead()
    Track.clean_dcheck_dead()
    ReleaseTrack.clean_dead()
    Release.clean_dead()
    Artist.clean_dead()


def change_in_lib_to_downloaded():
    def is_in_lib(t: Track) -> bool:
        for content_track in t.content_tracks.all():
            content_track: ContentTrack
            if content_track.content_item.content_list.name == RELAX_N_LISTEN_LIST:
                return True
        return False

    lib_list = None
    for cl in ContentList.objects.all():
        if cl.name == RELAX_N_LISTEN_LIST:
            lib_list = cl
            break

    if lib_list is None:
        raise ValueError(f"Failed to find content list: {RELAX_N_LISTEN_LIST}")

    tracks = Track.objects.all()

    for track in tracks:
        status = TrackStatus.from_str(track.status)
        if status == TrackStatus.IN_LIBRARY and not is_in_lib(track):
            track.status = TrackStatus.DOWNLOADED.value
            track.save()


def assign_release_artist():
    releases = Release.objects.all()
    for release in releases:
        position = 1
        release.artists2.clear()
        for artist in release.artists.all():
            ReleaseArtists.objects.create(release=release, artist=artist, position=position)
            position += 1


def run_short_scripts():
    short_scripts.__main__()


def get_last_modified():
    items = ContentItem.objects.all().order_by("-modified_at")[0:50]
    for item in items:
        print(item.id, item.url, item.modified_at)


def get_last_watched():
    items = Video.objects.all().filter(watched_date__isnull=False, status=WatchingStatus.FINISHED.value).order_by(
        "-watched_date")[0:50]
    for item in items:
        print(item.id, item.name, item.rating, item.watched_date)


def update_music_items():
    def get_music_item_by_pk(pk: int) -> ContentMusicItem:
        return ContentMusicItem.objects.get(pk=pk)

    # item = get_music_item_by_pk(333399)
    # item.title = "Tony Mahoney - Intro (NOTE: not the actual name of song)"
    # item.save()


def normalize_text_in_file():
    data = file.read(NORMALIZATION_PATH, encoding=file.ENCODING_UTF8)
    result_data = [normalize_text(line) for line in data]
    file.write(NORMALIZATION_PATH, result_data, encoding=file.ENCODING_UTF8)


class Command(BaseCommand):
    def handle(self, **options):
        pass
        normalize_text_in_file()
        # items = ContentMusicItem.objects.filter_by_content_list(57).order_by("position")
        # print(items.count())
        # for i, item in enumerate(items, start=1):
        #     item: ContentMusicItem
        #     if i != item.position:
        #         print(item.id, i, item.position, item.title)
        #         break

        # tracks = Track.objects.filter(title__icontains="ice of Autum")
        # for track in tracks:
        #     print(track)

        # assign_release_artist()

        # debug_import()
        # clean_dead_music()
        # print_dead_tracks()
        # print_counts()
        # clean_music()
        # __main__()
