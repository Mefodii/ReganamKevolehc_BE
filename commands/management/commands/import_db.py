import os

import tablib
from django.core.management.base import BaseCommand
from import_export.resources import ModelResource

from contenting.resources import ContentListResource, ContentWatcherResource, ContentItemResource, \
    ContentMusicItemResource, ContentTrackResource
from listening.resources import ArtistResource, TrackResource, ReleaseTrackResource, ReleaseResource
from notes.resources import NoteResource
from utils import file
from watching.resources import VideoResource, ImageModelResource, GroupResource

BACKUPS_PATH = "backups\\"
MEDIA_PATH = 'media'


def import_table(resource: ModelResource, export_name: str):
    json_file = export_name + '.json'
    data = file.read_json(json_file)
    dataset = tablib.Dataset().load(data)
    resource.import_data(dataset)


# noinspection DuplicatedCode
def import_tables(import_ts: str):
    resources = [
        # Watching
        [GroupResource(), "Group - " + import_ts],
        [VideoResource(), "Video - " + import_ts],
        [ImageModelResource(), "Image - " + import_ts],
        # Note
        [NoteResource(), "Note - " + import_ts],
        # Listening
        [ArtistResource(), "Artist - " + import_ts],
        [TrackResource(), "Track - " + import_ts],
        [ReleaseTrackResource(), "ReleaseTrack - " + import_ts],
        [ReleaseResource(), "Release - " + import_ts],
        # Contenting
        [ContentListResource(), "ContentList - " + import_ts],
        [ContentWatcherResource(), "ContentWatcher - " + import_ts],
        [ContentItemResource(), "ContentItem - " + import_ts],
        [ContentMusicItemResource(), "ContentMusicItem - " + import_ts],
        [ContentTrackResource(), "ContentTrack - " + import_ts],
    ]

    res_len = len(resources)
    for i in range(res_len):
        resource = resources[i]
        print(f"Importing resource {i + 1}/{res_len} - {resource[1]}")
        import_table(resource[0], resource[1])


class Command(BaseCommand):
    def handle(self, **options):
        cwd = os.getcwd()
        import_ts = "2024-07-16"
        backup_path = f"{BACKUPS_PATH}backup - {import_ts}"
        os.chdir(backup_path)

        import_tables(import_ts)
        os.chdir(cwd)
