from django.core.management.base import BaseCommand
from django.db.models import QuerySet

from constants import paths
from constants.constants import TEST_WATCHER_ID
from contenting.models import ContentWatcher
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.django_manager import YoutubeWatcherDjangoManager
from contenting.reganam_tnetnoc.watchers.youtube.manager import YoutubeWatchersManager

dk_file = paths.API_KEY_PATH
worker = YoutubeWorker(dk_file)


def run_imported_watchers():
    watchers: QuerySet[ContentWatcher] = ContentWatcher.objects.all()
    for watcher in watchers:
        if watcher.watcher_id.startswith(TEST_WATCHER_ID):
            continue

        if watcher.watcher_id != "UCGRB1ZjIqAiaGwt-XLq9CnA":
            continue

        manager = YoutubeWatcherDjangoManager(worker, watcher, log_file=paths.YOUTUBE_API_LOG)
        manager.run_updates()


def run_json_watchers():
    watcher_files = [
        paths.YOUTUBE_WATCHERS_PATH,
        # paths.YOUTUBE_WATCHERS_PGM_PATH,
    ]

    for watcher_file in watcher_files:
        manager = YoutubeWatchersManager(worker, watcher_file, paths.YOUTUBE_API_LOG)
        manager.run_updates()


class Command(BaseCommand):
    def handle(self, **options):
        pass
        run_imported_watchers()
        # run_json_watchers()
