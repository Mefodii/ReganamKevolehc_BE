from typing import TypeVar

from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import QuerySet

from commands.management.commands.run_watcher_import import RELAX_N_LISTEN_LIST
from constants.enums import TrackStatus
from contenting.models import ContentTrack, ContentMusicItem, ContentList
from listening.models import Track, Artist, ReleaseTrack, Release
from utils import file


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


def clean_music():
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


class Command(BaseCommand):
    def handle(self, **options):
        pass
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

        # tracks = Track.objects.filter(title="Music Is Mine")
        # for track in tracks:
        #     print(track)

        # debug_import()
        # clean_dead_music()
        # print_dead_tracks()
        print_counts()
        # clean_music()
        # __main__()
