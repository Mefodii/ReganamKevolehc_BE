from django.core.management.base import BaseCommand

from constants import paths
from contenting.models import ContentWatcher
from contenting.reganam_tnetnoc.watchers.youtube.api import YoutubeWorker
from contenting.reganam_tnetnoc.watchers.youtube.django_manager import YoutubeWatcherDjangoManager

dk_file = paths.API_KEY_PATH
worker = YoutubeWorker(dk_file)


class Command(BaseCommand):
    def handle(self, **options):
        watchers = ContentWatcher.objects.all()
        for watcher in watchers:
            if watcher.download:
                # TODO: implement for downloadable watchers
                continue

            manager = YoutubeWatcherDjangoManager(worker, watcher, log_file=paths.YOUTUBE_API_LOG)
            manager.run_updates()
