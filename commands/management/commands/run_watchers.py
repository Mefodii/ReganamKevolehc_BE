from pprint import pprint

from django.core.management.base import BaseCommand

from contenting.models import ContentWatcher


class Command(BaseCommand):
    def handle(self, **options):
        watchers = ContentWatcher.objects.all()
        pprint(watchers)
