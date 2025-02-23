from django.core.management.base import BaseCommand

from contenting.reganam_tnetnoc.main import simple_download


class Command(BaseCommand):
    def handle(self, **options):
        pass
        simple_download.__main__(None)
